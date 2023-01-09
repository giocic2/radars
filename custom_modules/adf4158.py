from math import log2

# Parameters for FMCW radar (triengle chirp)
### User Input
VCO_FREQUENCY_START = 23.5e9 # Hz
VCO_FREQUENCY_STOP = 24.5e9 # Hz
PRESCALER_RATIO = 1/16
UPCHIRP_WAIT_TIME = 0 # s
UPCHIRP_TIME = 1.25e-3 # s
UPCHIRP_NUMBER_OF_STEPS = 1000
REF_IN_FREQUENCY = 10e6 # Hz
### End of User Input
print("FMCW ramp parameters (triangle chirp):")
print("VCO frequency start: {:e} Hz".format(VCO_FREQUENCY_START))
print("VCO frequency stop: {:e} Hz".format(VCO_FREQUENCY_STOP))
vcoSweep = VCO_FREQUENCY_STOP - VCO_FREQUENCY_START # Hz
print("VCO sweep: {:e} Hz".format(vcoSweep))
print("Prescaler ratio: {:}".format(PRESCALER_RATIO.as_integer_ratio()))
pllFrequencyStart = VCO_FREQUENCY_START*PRESCALER_RATIO # Hz
print("PLL frequency start: {:e} Hz".format(pllFrequencyStart))
pllFrequencyStop = VCO_FREQUENCY_STOP*PRESCALER_RATIO # Hz
print("PLL frequency stop: {:e} Hz".format(pllFrequencyStop))
pllSweep = pllFrequencyStop - pllFrequencyStart # Hz
print("PLL sweep: {:e} Hz".format(pllSweep))
print("Chirp time (up-chirp): {:e} s".format(UPCHIRP_TIME))
print("Wait time before up-chirp: {:e} s".format(UPCHIRP_WAIT_TIME))
modulationPeriod = UPCHIRP_WAIT_TIME + UPCHIRP_TIME*2 # s
print("Modulation period: {:e} s".format(modulationPeriod))
print("Number of steps (up-chirp): {:d}".format(UPCHIRP_NUMBER_OF_STEPS))
stepDuration = UPCHIRP_TIME/UPCHIRP_NUMBER_OF_STEPS # s
print("Step duration: {:e} s".format(stepDuration))
vcoStepDeviation = (VCO_FREQUENCY_STOP - VCO_FREQUENCY_START)/UPCHIRP_NUMBER_OF_STEPS # Hz
print("Step deviation (VCO): {:e} Hz".format(vcoStepDeviation))
pllStepDeviation = vcoStepDeviation*PRESCALER_RATIO # Hz
print("Step deviation (PLL): {:e} Hz".format(pllStepDeviation))
print("IF frequency of static target: {:e} Hz/m".format(2*vcoSweep/3e8/UPCHIRP_TIME))

# ADF4158 parameters
print("\nADF4158 parameters:")
# PFD settings
RDIV2_ENABLED = False # This can be used to provide a 50% duty cycle signal at the PFD for use with cycle slip reduction
CYCLE_SLIP_REDUCTION_ENABLED = False # method for improving lock times
REFERENCE_DOUBLER_ENABLED = True # Multiplies REF_IN by 2
R_COUNTER = 1 # 5-bit word (integer value from 1 to 32). Divide down the REF_IN frequency by this value, to produce the PFD frequency
pfdFrequency = REF_IN_FREQUENCY * ((1 + REFERENCE_DOUBLER_ENABLED)/(R_COUNTER*(1 + RDIV2_ENABLED))) # Hz
print("PFD frequency: {:e} Hz".format(pfdFrequency))
pllResolution = pfdFrequency/2**25 # Hz
print("Frequency resolution (PLL): {:e} Hz".format(pllResolution))
vcoResolution = pllResolution/PRESCALER_RATIO # Hz
print("Frequency resolution (VCO): {:e} Hz".format(vcoResolution))


# Charge pump settings
RESISTOR_CHARGE_PUMP = 5.1e3 # Ohm
CHARGE_PUMP_LEVEL = 7 # 4-bit word (integer value from 0 to 15)
MAX_CHARGE_PUMP_CURRENT = 25.5/RESISTOR_CHARGE_PUMP # A
print("Charge Pump Current = {:e} A".format((CHARGE_PUMP_LEVEL+1)*MAX_CHARGE_PUMP_CURRENT/16))
CHARGE_PUMP_THREESTATE_ENABLED = False # set to False for normal operation

# Other settings
MUXOUT_CTRL = 0 # 4-bit word (integer between 0 and 15)
                # 0: 3-state output
                # 1: digital VDD
                # 2: digital GND
                # 3: R divider output
                # 4: N divider output
                # 5: reserved
                # 6: digital lock detect
                # 7: serial data output
                # 8: reserved
                # 9: reserved
                # 10: CLK divider output
                # 11: reserved
                # 12: fast-lock switch
                # 13: R divider / 2
                # 14: N divider / 2
                # 15: readback to MUXOUT
N_SEL = False # additional delay to the loading of the INT value, to circumvent the issue of pipeline delay
SD_NOT_RESET = False # control the reset of sigma-delta modulator on each write of R0 register. If True, the sigma-delta modulator is NOT reset.
LDP = 0     # Lock Detect Precision.
            # 0: 24 PFD cycles before digital lock detect is set
            # 1: 40 PFD cycles before digital lock detect is set
PHASE_DETECTOR_POLARITY = 0   # 1-bit word 
                            # 0: VCO characteristics are positive
                            # 1: VCO characteristics are negative
POWER_DOWN_ENABLED = False # the registers values are retained, but the ADF4158 is disabled (three-state mode).
COUNTER_RESET = False # when True, the synthesizer counters are held to reset.
LOAD_ENABLE_SYNC = False # when True, the load enable pin is synchronized with the REF_IN signal.
SD_MODULATOR_MODE = 0b00000   # 5-bit word, only two values allowed.
                        # 0b00000: normal operation
                        # 0b01110: ADF4158 in integer-N mode. Ramping, PSK, FKS and phase adjust are disabled.
if SD_MODULATOR_MODE == 0b01110:
    print("ADF4158 in integer-N mode. Ensure to write R3 twice to trigger a counter reset: once with COUNTER_RESET = True, and then with COUNTER_RESET = False.")
NEGATIVE_BLEED_CURRENT = 0b00   # 2-bit word, only two values allowed. Ensures that the charge pump operates outof the dead zone.
                                # 0b00: OFF
                                # 0b11: ON
READBACK_TO_MUXOUT = 0b00       # 2-bit word, only two values allowed. Allows reading back the synthesizer's frequency at the moment of interrupt (MUXOUT_CTRL=0b1111).
                                # 0b00: OFF
                                # 0b10: ON

# Time settings
CLK2 = 1 # 12-bit word (integer between 1 and 4095). Used in ramp mode and in fast-lock mode.
assert CLK2 >= 1 and CLK2 <= 4095, "CLK2 must be an integer between 1 and 4095"
CLK1 = round(stepDuration*pfdFrequency/CLK2) # 12-bit word (integer between 1 and 4095). Used in ramp mode.
while CLK1 > 4095:
    CLK2=CLK2+1
    assert CLK2 >= 1 and CLK2 <= 4095, "CLK2 must be an integer between 1 and 4095"
    CLK1 = round(stepDuration*pfdFrequency/CLK2) # 12-bit word (integer between 1 and 4095). Used in ramp mode.
assert CLK1 >= 1 and CLK1 <= 4095, "CLK1 must be an integer between 1 and 4095"
CLOCK_DIVIDER_MODE = 0b00   # 2-bit word (integer between 0 and 3)
                            # 0b00: clock divider off
                            # 0b01: fast-lock divider
                            # 0b10: reserved
                            # 0b11: ramp divider
TX_RAMP_CLK = 0 # 1-bit word
                # 0: clock divider clock is used for clocking the ramp
                # 1: TX_DATA clock is used for clocking the ramp
RAMP_DELAY_FAST_LOCK_ENABLED = False
RAMP_DELAY_ENABLED = False
DELAY_CLOCK_SELECT = 0  # 1-bit word
                        # 0: PFD clock is used for the delay
                        # 1: PFD*CLK1 is used for the delay
DELAYED_START_ENABLED = False
DELAYED_START_WORD = 0 # 12-bit word (integer between 0 and 4095)

# Frequency settings
if pllFrequencyStop <= 3e9: # dual-modulus prescaler depends on maximum PLL frequency 
    N_MIN = 23
    PRESCALER_BIT = 0 # 4/5 dual-modulus prescaler
else:
    N_MIN = 75
    PRESCALER_BIT = 1 # 8/9 dual-modulus prescaler
INT = int(pllFrequencyStart/pfdFrequency) # 12-bit word (integer between 23 and 4095)
assert INT >= N_MIN and INT <= 4095, "INT must be an integer between N_MIN and 4095"
FRAC = round((pllFrequencyStart/pfdFrequency - INT)*2**25) # 25-bit word (integer between 0 and 33_554_431)
assert FRAC >=0 and FRAC <= 33_554_431, "FRAC must be an integer between 0 and 33_554_431"
pllFrequency = pfdFrequency * (INT + (FRAC/2**25)) # Hz
print("Synthesized PLL frequency (start) = {:e} Hz".format(pllFrequency))
print("Synthesized VCO frequency (start)= {:e} Hz".format(pllFrequency/PRESCALER_RATIO))
RAMP_MODE = 1   # 2-bit word (integer between 0 and 3).
                # 0: continuous sawtooth
                # 1: continuous triangle
                # 2: single sawtooth
                # 3: single ramp burst
PSK_ENABLED = False # Toggle output phase between 0 and 180 degrees. TX_DATA (pin 12) controls the phase.  
FSK_ENABLED = False # N-divide value incremented and decremented by DEV*2^(DEV_OFFSET). TX_DATA (pin 12) controls the frequency shift.
PAR_RAMP_ENABLED = False # parabolic ramp mode
INTERRUPT = 0b00    # 2-bit word (integer between 0 and 3). Rising edge of TX_DATA (pin 12) triggers the interrupt.
                    # 0b00: interrupt disabled
                    # 0b01: load channel, continue sweep
                    # 0b10: not used
                    # 0b11: load channel, stop sweep

# Frequency modulation
RAMP_ENABLED = True
FSK_RAMP_ENABLED = False # FSK ramp mode
RAMP2_ENABLED = False # second ramp
if RAMP2_ENABLED:
    print("Ramp 2 is enabled. Ensure to load R5 twice, changing \'Deviation Select\' bit and '\Step select\' bit between the two writes.")
DEVIATION_SELECT_RAMP1 = 0b0
DEVIATION_SELECT_RAMP2 = 0b1
STEP_SELECT = 0b0 # 1-bit word
STEP = UPCHIRP_NUMBER_OF_STEPS # 20-bit word (integer between 0 and 1_048_575). Number of steps in the ramp.

DEV_OFFSET = round(log2((pllStepDeviation)/(pllResolution*(2**15)))) # 4-bit word (integer between 0 and 9)
assert DEV_OFFSET >= 0 and DEV_OFFSET <= 9, "DEV_OFFSET must be between 0 and 9"
DEV = round(pllStepDeviation/(pllResolution*(2**DEV_OFFSET))) # 16-bit CA2 word (integer between -32_768 and 32_767)
while DEV < -32_767 or DEV > 32_767:
    DEV_OFFSET = DEV_OFFSET+1
    assert DEV_OFFSET >= 0 and DEV_OFFSET <= 9, "DEV_OFFSET must be between 0 and 9"
    DEV = round(pllStepDeviation/(pllResolution*(2**DEV_OFFSET))) # 16-bit CA2 word (integer between -32_768 and 32_767)
assert DEV >= -32_768 and DEV <= 32_767, "DEV must be between -32_768 and 32_767"
frequencyDeviation = (pfdFrequency/2**25)*(DEV*DEV_OFFSET) # Hz. Frequency deviation for each frequency hop


# R0 register
print("\nR0 register settings:")
print("Ramp On = {:01b}".format(int(RAMP_ENABLED))) 
print("MuxOut Control = {:04b} (0x{:01x})".format(MUXOUT_CTRL, MUXOUT_CTRL))
print("INT = {:012b} (0x{:03x}) ({:d})".format(INT, INT, INT))
print("FRAC = {:025b} (0x{:07x}) ({:d})".format(FRAC, FRAC, FRAC))
FRAC_MSB = FRAC>>13 # 12-MSBs of FRAC
print("FRAC 12-MSBs = {:012b} (0x{:03x})".format(FRAC_MSB, FRAC_MSB))
CTRL_BITS_R0 = 0b000
print("Control bits: {:03b} (0x{:01x})".format(CTRL_BITS_R0, CTRL_BITS_R0))
R0_REGISTER = int(RAMP_ENABLED)<<31 | MUXOUT_CTRL<<27 | INT<<15 | FRAC_MSB<<3 | CTRL_BITS_R0
print("R0 register: {:032b} (0x{:08x})".format(R0_REGISTER, R0_REGISTER)) 

# R1 register
print("\nR1 register settings:")
FRAC_LSB = FRAC & 0b1_1111_1111_1111 # 13-LSBs of FRAC
print("FRAC 13-LSBs = {:013b} (0x{:04x})".format(FRAC_LSB, FRAC_LSB))
CTRL_BITS_R1 = 0b001
print("Control bits: {:03b} (0x{:01x})".format(CTRL_BITS_R1, CTRL_BITS_R1))
R1_REGISTER = FRAC_LSB<<15 | CTRL_BITS_R1
# Assert R0 and R1 register settings
assert (INT + (FRAC/2**25))>=N_MIN, "N must be greater than or equal to {}".format(N_MIN)
if SD_MODULATOR_MODE == 0b01110:
    assert FRAC == 0, "FRAC must be 0 when ADF4158 in integer-N mode (SD_MODULATOR_MODE is 0b01110)."
print("R1 register: {:032b} (0x{:08x})".format(R1_REGISTER, R1_REGISTER))

# R2 register
print("\nR2 register settings:")
print("Cycle Slip Reduction = {:01b}".format(CYCLE_SLIP_REDUCTION_ENABLED))
print("Charge Pump Level = {:04b} (0x{:01x})".format(CHARGE_PUMP_LEVEL, CHARGE_PUMP_LEVEL))
print("P = {:01b}".format(PRESCALER_BIT))
print("T (or RDIV2) = {:01b}".format(RDIV2_ENABLED))
print("D = {:01b}".format(REFERENCE_DOUBLER_ENABLED))
print("R = {:05b} (0x{:02x})".format(R_COUNTER%32, R_COUNTER%32))
print("CLK1 = {:012b} (0x{:03x}) ({:d})".format(CLK1, CLK1, CLK1))
CTRL_BITS_R2 = 0b010
print("Control bits: {:03b} (0x{:01x})".format(CTRL_BITS_R2, CTRL_BITS_R2))
R2_REGISTER = CYCLE_SLIP_REDUCTION_ENABLED<<28 | CHARGE_PUMP_LEVEL<<24 | PRESCALER_BIT<<22 | RDIV2_ENABLED<<21 | REFERENCE_DOUBLER_ENABLED<<20 | (R_COUNTER%32)<<15 | CLK1<<3 | CTRL_BITS_R2
# Assert R2 register settings
if CYCLE_SLIP_REDUCTION_ENABLED:
    assert RDIV2_ENABLED, "Cycle slip reduction requires RDIV2_ENABLED to be True"
if REFERENCE_DOUBLER_ENABLED:
    assert REF_IN_FREQUENCY <= 30e6, "REF_IN frequency must be less than or equal to 30 MHz"
print("R2 register: {:032b} (0x{:08x})".format(R2_REGISTER, R2_REGISTER))

# R3 register
print("\nR3 register settings:")
print("N SEL = {:01b}".format(N_SEL))
print("SD Reset = {:01b}".format(SD_NOT_RESET))
print("Ramp Mode = {:02b} (0x{:01x})".format(RAMP_MODE, RAMP_MODE))
print("PSK Enable = {:01b}".format(PSK_ENABLED))
print("FSK Enable = {:01b}".format(FSK_ENABLED))
print("LDP = {:01b}".format(LDP))
print("PD polarity = {:01b}".format(PHASE_DETECTOR_POLARITY))
print("Power-Down = {:01b}".format(POWER_DOWN_ENABLED))
print("Charge Pump Three-State = {:01b}".format(CHARGE_PUMP_THREESTATE_ENABLED))
print("Counter Reset = {:01b}".format(COUNTER_RESET))
CTRL_BITS_R3 = 0b011
print("Control bits: {:03b} (0x{:01x})".format(CTRL_BITS_R3, CTRL_BITS_R3))
R3_REGISTER = N_SEL<<15 | SD_NOT_RESET<<14 | RAMP_MODE<<10 | PSK_ENABLED<<9 | FSK_ENABLED<<8 | LDP<<7 | PHASE_DETECTOR_POLARITY<<6 | POWER_DOWN_ENABLED<<5 | CHARGE_PUMP_THREESTATE_ENABLED<<4 | COUNTER_RESET<<3 | CTRL_BITS_R3
print("R3 register: {:032b} (0x{:08x})".format(R3_REGISTER, R3_REGISTER))

# R4 register
print("\nR4 register settings:")
print("LE SEL = {:01b}".format(LOAD_ENABLE_SYNC))
print("SD Modulator Mode: {:05b}".format(SD_MODULATOR_MODE))
print("Negative Bleed Current: {:02b}".format(NEGATIVE_BLEED_CURRENT))
print("Readback to MUXOUT: {:02b}".format(READBACK_TO_MUXOUT))
print("Clock Divider (DIV) Mode: {:02b}".format(CLOCK_DIVIDER_MODE))
print("CLK2 = {:012b} (0x{:03x}) ({:d})".format(CLK2, CLK2, CLK2))
CTRL_BITS_R4 = 0b100
print("Control bits: {:03b} (0x{:01x})".format(CTRL_BITS_R4, CTRL_BITS_R4))
# Assert R4 register settings
if NEGATIVE_BLEED_CURRENT == 0b11:
    assert READBACK_TO_MUXOUT == 0b00, "READBACK_TO_MUXOUT must be 0b00 when NEGATIVE_BLEED_CURRENT is 0b11."
R4_REGISTER = LOAD_ENABLE_SYNC<<31 | SD_MODULATOR_MODE<<26 | NEGATIVE_BLEED_CURRENT<<23 | READBACK_TO_MUXOUT<<21 | CLOCK_DIVIDER_MODE<<19 | CLK2<<7 | CTRL_BITS_R4
print("R4 register: {:032b} (0x{:08x})".format(R4_REGISTER, R4_REGISTER))

# R5 register
print("\nR5 register settings:")
print("Tx Ramp CLK = {:01b}".format(TX_RAMP_CLK))
print("PAR Ramp: {:01b}".format(PAR_RAMP_ENABLED))
print("Interrupt: {:02b}".format(INTERRUPT))
print("FSK Ramp Enable: {:01b}".format(FSK_RAMP_ENABLED))
print("Ramp 2 Enable: {:01b}".format(RAMP2_ENABLED))
print("Deviation Select (load 1): {:01b}".format(DEVIATION_SELECT_RAMP1))
print("Deviation Select (load 2): {:01b}".format(DEVIATION_SELECT_RAMP2))
print("Deviation Offset Word: {:04b} (0x{:01x}) ({:d})".format(DEV_OFFSET, DEV_OFFSET, DEV_OFFSET))
print("Deviation Word: {:016b} (0x{:04x}) ({:d})".format((DEV+32_768 ^ 0b1<<15), (DEV+32_768 ^ 0b1<<15), (DEV+32_768 ^ 0b1<<15)))
CTRL_BITS_R5 = 0b101
print("Control bits: {:03b} (0x{:01x})".format(CTRL_BITS_R5, CTRL_BITS_R5))
R5_REGISTER_LOAD1 = TX_RAMP_CLK<<29 | PAR_RAMP_ENABLED<<28 | INTERRUPT<<26 | FSK_RAMP_ENABLED<<25 | RAMP2_ENABLED<<24 | DEVIATION_SELECT_RAMP1<<23 | DEV_OFFSET<<19 | (DEV+32_768 ^ 0b1<<15)<<3 | CTRL_BITS_R5
print("R5 register (load 1): {:032b} (0x{:08x})".format(R5_REGISTER_LOAD1, R5_REGISTER_LOAD1))

# R6 register
print("\nR6 register settings:")
print("Step SEL: {:01b}".format(STEP_SELECT))
print("Step Work: {:020b} (0x{:05x})".format(STEP, STEP))
CTRL_BITS_R6 = 0b110
print("Control bits: {:03b} (0x{:01x})".format(CTRL_BITS_R6, CTRL_BITS_R6))
R6_REGISTER = STEP_SELECT<<23 | STEP<<3 | CTRL_BITS_R6
print("R6 register: {:032b} (0x{:08x})".format(R6_REGISTER, R6_REGISTER))

# R7 register
print("\nR7 register settings:")
print("Ramp Delay Fast Lock: {:01b}".format(RAMP_DELAY_FAST_LOCK_ENABLED))
print("Ramp Delay: {:01b}".format(RAMP_DELAY_ENABLED))
print("Delay Clock Select: {:01b}".format(DELAY_CLOCK_SELECT))
print("Delayed Start Enable: {:01b}".format(DELAYED_START_ENABLED))
print("Delayed Start Word: {:016b} (0x{:04x})".format(DELAYED_START_WORD, DELAYED_START_WORD))
CTRL_BITS_R7 = 0b111
print("Control bits: {:03b} (0x{:01x})".format(CTRL_BITS_R7, CTRL_BITS_R7))
R7_REGISTER = RAMP_DELAY_FAST_LOCK_ENABLED<<18 | RAMP_DELAY_ENABLED<<17 | DELAY_CLOCK_SELECT<<16 | DELAYED_START_ENABLED<<15 | DELAYED_START_WORD<<3 | CTRL_BITS_R7
print("R7 register: {:032b} (0x{:08x})".format(R7_REGISTER, R7_REGISTER))

# Parameters for ADIsimPLL simulation
print("\nParameters for ADIsimPLL simulation:")
print("CLK1: {:d}".format(CLK1))
print("CLK2: {:d}".format(CLK2))
print("DEV: {:d}".format((DEV+32_768 ^ 0b1<<15)))
print("DEV_OFFSET: {:d}".format(DEV_OFFSET))
print("Number of steps: {:d}".format(UPCHIRP_NUMBER_OF_STEPS))