from skoolkittest import SkoolKitTestCase
from skoolkit.comment import CommentGenerator

IX_01 = '(#REGix+#N(1,2,,1)($))'
IX_FF = '(#REGix-#N(1,2,,1)($))'
BITS = tuple(tuple(b for b in range(8) if (n >> b) % 2) for n in range(256))

RLC = 'Rotate {} left circular (copying bit 7 into bit 0 and into the carry flag)'
RLC_r = 'Rotate {} left circular (copying bit 7 into bit 0 and into the carry flag) and copy the result to #REG{}'
RRC = 'Rotate {} right circular (copying bit 0 into bit 7 and into the carry flag)'
RRC_r = 'Rotate {} right circular (copying bit 0 into bit 7 and into the carry flag) and copy the result to #REG{}'
RL = 'Rotate {} left through the carry flag'
RL_r = 'Rotate {} left through the carry flag and copy the result to #REG{}'
RR = 'Rotate {} right through the carry flag'
RR_r = 'Rotate {} right through the carry flag and copy the result to #REG{}'
SLA = 'Shift {} left (copying bit 7 into the carry flag, and resetting bit 0)'
SLA_r = 'Shift {} left (copying bit 7 into the carry flag, and resetting bit 0) and copy the result to #REG{}'
SRA = 'Shift {} right (copying bit 0 into the carry flag, and leaving bit 7 unchanged)'
SRA_r = 'Shift {} right (copying bit 0 into the carry flag, and leaving bit 7 unchanged) and copy the result to #REG{}'
SLL = 'Shift {} left (copying bit 7 into the carry flag, and setting bit 0)'
SLL_r = 'Shift {} left (copying bit 7 into the carry flag, and setting bit 0) and copy the result to #REG{}'
SRL = 'Shift {} right (copying bit 0 into the carry flag, and resetting bit 7)'
SRL_r = 'Shift {} right (copying bit 0 into the carry flag, and resetting bit 7) and copy the result to #REG{}'
BIT = 'Set the zero flag if bit {} of {} is 0'
RES = 'Reset bit {} of {}'
RES_r = 'Reset bit {} of {} and copy the result to #REG{}'
SET = 'Set bit {} of {}'
SET_r = 'Set bit {} of {} and copy the result to #REG{}'

INSTRUCTIONS = {
    '00': "Do nothing",
    '010000': "#REGbc=#N(0,4,,1)($)",
    '02': "POKE #REGbc,#REGa",
    '03': "#REGbc=#REGbc+1",
    '04': "#REGb=#REGb+1",
    '05': "#REGb=#REGb-1",
    '0600': "#REGb=#N(0,2,,1)($)",
    '07': "Rotate #REGa left circular (copying bit 7 into bit 0 and into the carry flag)",
    '08': "Exchange #REGaf and #REGaf'",
    '09': "#REGhl=#REGhl+#REGbc",
    '0A': "#REGa=PEEK #REGbc",
    '0B': "#REGbc=#REGbc-1",
    '0C': "#REGc=#REGc+1",
    '0D': "#REGc=#REGc-1",
    '0E00': "#REGc=#N(0,2,,1)($)",
    '0F': "Rotate #REGa right circular (copying bit 0 into bit 7 and into the carry flag)",
    '1000': "Decrement #REGb and jump to #R32770 if #REGb>0",
    '110000': "#REGde=#N(0,4,,1)($)",
    '12': "POKE #REGde,#REGa",
    '13': "#REGde=#REGde+1",
    '14': "#REGd=#REGd+1",
    '15': "#REGd=#REGd-1",
    '1600': "#REGd=#N(0,2,,1)($)",
    '17': "Rotate #REGa left through the carry flag",
    '1802': "Jump to #R32772",
    '19': "#REGhl=#REGhl+#REGde",
    '1A': "#REGa=PEEK #REGde",
    '1B': "#REGde=#REGde-1",
    '1C': "#REGe=#REGe+1",
    '1D': "#REGe=#REGe-1",
    '1E00': "#REGe=#N(0,2,,1)($)",
    '1F': "Rotate #REGa right through the carry flag",
    '20FE': "Jump to #R32768 if the zero flag is not set",
    '210000': "#REGhl=#N(0,4,,1)($)",
    '220000': "POKE #N(0,4,,1)($),#REGl; POKE #N(1,4,,1)($),#REGh",
    '23': "#REGhl=#REGhl+1",
    '24': "#REGh=#REGh+1",
    '25': "#REGh=#REGh-1",
    '2600': "#REGh=#N(0,2,,1)($)",
    '27': "Decimal adjust #REGa",
    '2802': "Jump to #R32772 if the zero flag is set",
    '29': "#REGhl=#REGhl+#REGhl",
    '2AFFFF': "#REGl=PEEK #N(65535,4,,1)($); #REGh=PEEK #N(0,4,,1)($)",
    '2B': "#REGhl=#REGhl-1",
    '2C': "#REGl=#REGl+1",
    '2D': "#REGl=#REGl-1",
    '2E00': "#REGl=#N(0,2,,1)($)",
    '2F': "#REGa=#N($FF,2,,1)($)-#REGa",
    '30FE': "Jump to #R32768 if the carry flag is not set",
    '310000': "#REGsp=#N(0,4,,1)($)",
    '320000': "POKE #N(0,4,,1)($),#REGa",
    '33': "#REGsp=#REGsp+1",
    '34': "POKE #REGhl,(PEEK #REGhl)+1",
    '35': "POKE #REGhl,(PEEK #REGhl)-1",
    '3600': "POKE #REGhl,#N(0,2,,1)($)",
    '37': "Set the carry flag",
    '3802': "Jump to #R32772 if the carry flag is set",
    '39': "#REGhl=#REGhl+#REGsp",
    '3A0000': "#REGa=PEEK #N(0,4,,1)($)",
    '3B': "#REGsp=#REGsp-1",
    '3C': "#REGa=#REGa+1",
    '3D': "#REGa=#REGa-1",
    '3E00': "#REGa=#N(0,2,,1)($)",
    '3F': "Complement the carry flag",
    '40': "Do nothing",
    '41': "#REGb=#REGc",
    '42': "#REGb=#REGd",
    '43': "#REGb=#REGe",
    '44': "#REGb=#REGh",
    '45': "#REGb=#REGl",
    '46': "#REGb=PEEK #REGhl",
    '47': "#REGb=#REGa",
    '48': "#REGc=#REGb",
    '49': "Do nothing",
    '4A': "#REGc=#REGd",
    '4B': "#REGc=#REGe",
    '4C': "#REGc=#REGh",
    '4D': "#REGc=#REGl",
    '4E': "#REGc=PEEK #REGhl",
    '4F': "#REGc=#REGa",
    '50': "#REGd=#REGb",
    '51': "#REGd=#REGc",
    '52': "Do nothing",
    '53': "#REGd=#REGe",
    '54': "#REGd=#REGh",
    '55': "#REGd=#REGl",
    '56': "#REGd=PEEK #REGhl",
    '57': "#REGd=#REGa",
    '58': "#REGe=#REGb",
    '59': "#REGe=#REGc",
    '5A': "#REGe=#REGd",
    '5B': "Do nothing",
    '5C': "#REGe=#REGh",
    '5D': "#REGe=#REGl",
    '5E': "#REGe=PEEK #REGhl",
    '5F': "#REGe=#REGa",
    '60': "#REGh=#REGb",
    '61': "#REGh=#REGc",
    '62': "#REGh=#REGd",
    '63': "#REGh=#REGe",
    '64': "Do nothing",
    '65': "#REGh=#REGl",
    '66': "#REGh=PEEK #REGhl",
    '67': "#REGh=#REGa",
    '68': "#REGl=#REGb",
    '69': "#REGl=#REGc",
    '6A': "#REGl=#REGd",
    '6B': "#REGl=#REGe",
    '6C': "#REGl=#REGh",
    '6D': "Do nothing",
    '6E': "#REGl=PEEK #REGhl",
    '6F': "#REGl=#REGa",
    '70': "POKE #REGhl,#REGb",
    '71': "POKE #REGhl,#REGc",
    '72': "POKE #REGhl,#REGd",
    '73': "POKE #REGhl,#REGe",
    '74': "POKE #REGhl,#REGh",
    '75': "POKE #REGhl,#REGl",
    '76': "Wait for the next interrupt",
    '77': "POKE #REGhl,#REGa",
    '78': "#REGa=#REGb",
    '79': "#REGa=#REGc",
    '7A': "#REGa=#REGd",
    '7B': "#REGa=#REGe",
    '7C': "#REGa=#REGh",
    '7D': "#REGa=#REGl",
    '7E': "#REGa=PEEK #REGhl",
    '7F': "Do nothing",
    '80': "#REGa=#REGa+#REGb",
    '81': "#REGa=#REGa+#REGc",
    '82': "#REGa=#REGa+#REGd",
    '83': "#REGa=#REGa+#REGe",
    '84': "#REGa=#REGa+#REGh",
    '85': "#REGa=#REGa+#REGl",
    '86': "#REGa=#REGa+PEEK #REGhl",
    '87': "#REGa=#REGa+#REGa",
    '88': "#REGa=#REGa+carry+#REGb",
    '89': "#REGa=#REGa+carry+#REGc",
    '8A': "#REGa=#REGa+carry+#REGd",
    '8B': "#REGa=#REGa+carry+#REGe",
    '8C': "#REGa=#REGa+carry+#REGh",
    '8D': "#REGa=#REGa+carry+#REGl",
    '8E': "#REGa=#REGa+carry+PEEK #REGhl",
    '8F': "#REGa=#REGa+carry+#REGa",
    '90': "#REGa=#REGa-#REGb",
    '91': "#REGa=#REGa-#REGc",
    '92': "#REGa=#REGa-#REGd",
    '93': "#REGa=#REGa-#REGe",
    '94': "#REGa=#REGa-#REGh",
    '95': "#REGa=#REGa-#REGl",
    '96': "#REGa=#REGa-PEEK #REGhl",
    '97': "#REGa=0",
    '98': "#REGa=#REGa-carry-#REGb",
    '99': "#REGa=#REGa-carry-#REGc",
    '9A': "#REGa=#REGa-carry-#REGd",
    '9B': "#REGa=#REGa-carry-#REGe",
    '9C': "#REGa=#REGa-carry-#REGh",
    '9D': "#REGa=#REGa-carry-#REGl",
    '9E': "#REGa=#REGa-carry-PEEK #REGhl",
    '9F': "#REGa=#N($FF,2,,1)($) if carry flag is set, 0 otherwise",
    'A0': "#REGa=#REGa&#REGb",
    'A1': "#REGa=#REGa&#REGc",
    'A2': "#REGa=#REGa&#REGd",
    'A3': "#REGa=#REGa&#REGe",
    'A4': "#REGa=#REGa&#REGh",
    'A5': "#REGa=#REGa&#REGl",
    'A6': "#REGa=#REGa&PEEK #REGhl",
    'A7': "Clear the carry flag and set the zero flag if #REGa=0",
    'A8': "#REGa=#REGa^#REGb",
    'A9': "#REGa=#REGa^#REGc",
    'AA': "#REGa=#REGa^#REGd",
    'AB': "#REGa=#REGa^#REGe",
    'AC': "#REGa=#REGa^#REGh",
    'AD': "#REGa=#REGa^#REGl",
    'AE': "#REGa=#REGa^PEEK #REGhl",
    'AF': "#REGa=0",
    'B0': "#REGa=#REGa|#REGb",
    'B1': "#REGa=#REGa|#REGc",
    'B2': "#REGa=#REGa|#REGd",
    'B3': "#REGa=#REGa|#REGe",
    'B4': "#REGa=#REGa|#REGh",
    'B5': "#REGa=#REGa|#REGl",
    'B6': "#REGa=#REGa|PEEK #REGhl",
    'B7': "Clear the carry flag and set the zero flag if #REGa=0",
    'B8': "Set the zero flag if #REGa=#REGb, or the carry flag if #REGa<#REGb",
    'B9': "Set the zero flag if #REGa=#REGc, or the carry flag if #REGa<#REGc",
    'BA': "Set the zero flag if #REGa=#REGd, or the carry flag if #REGa<#REGd",
    'BB': "Set the zero flag if #REGa=#REGe, or the carry flag if #REGa<#REGe",
    'BC': "Set the zero flag if #REGa=#REGh, or the carry flag if #REGa<#REGh",
    'BD': "Set the zero flag if #REGa=#REGl, or the carry flag if #REGa<#REGl",
    'BE': "Set the zero flag if #REGa=PEEK #REGhl, or the carry flag if #REGa<PEEK #REGhl",
    'BF': "Clear the carry flag and set the zero flag",
    'C0': "Return if the zero flag is not set",
    'C1': "Pop last item from stack into #REGbc",
    'C20000': "Jump to #R0 if the zero flag is not set",
    'C30000': "Jump to #R0",
    'C40000': "CALL #R0 if the zero flag is not set",
    'C5': "Push #REGbc onto the stack",
    'C600': "#REGa=#REGa+#N(0,2,,1)($)",
    'C7': "CALL #R0",
    'C8': "Return if the zero flag is set",
    'C9': "Return",
    'CA0000': "Jump to #R0 if the zero flag is set",
    'CC0000': "CALL #R0 if the zero flag is set",
    'CD0000': "CALL #R0",
    'CE00': "#REGa=#REGa+carry+#N(0,2,,1)($)",
    'CF': "CALL #R8",
    'D0': "Return if the carry flag is not set",
    'D1': "Pop last item from stack into #REGde",
    'D20000': "Jump to #R0 if the carry flag is not set",
    'D300': "OUT #N(0,2,,1)($),#REGa",
    'D40000': "CALL #R0 if the carry flag is not set",
    'D5': "Push #REGde onto the stack",
    'D600': "#REGa=#REGa-#N(0,2,,1)($)",
    'D7': "CALL #R16",
    'D8': "Return if the carry flag is set",
    'D9': "Exchange #REGbc, #REGde and #REGhl with #REGbc', #REGde' and #REGhl'",
    'DA0000': "Jump to #R0 if the carry flag is set",
    'DB00': "#REGa=IN (#N(256,,,1)($)*#REGa+#N(0,2,,1)($))",
    'DC0000': "CALL #R0 if the carry flag is set",
    'DE00': "#REGa=#REGa-carry-#N(0,2,,1)($)",
    'DF': "CALL #R24",
    'E0': "Return if the parity/overflow flag is not set (parity odd)",
    'E1': "Pop last item from stack into #REGhl",
    'E20000': "Jump to #R0 if the parity/overflow flag is not set (parity odd)",
    'E3': "Exchange the last item on the stack with #REGhl",
    'E40000': "CALL #R0 if the parity/overflow flag is not set (parity odd)",
    'E5': "Push #REGhl onto the stack",
    'E600': "#REGa=0",
    'E7': "CALL #R32",
    'E8': "Return if the parity/overflow flag is set (parity even)",
    'E9': "Jump to #REGhl",
    'EA0000': "Jump to #R0 if the parity/overflow flag is set (parity even)",
    'EB': "Exchange #REGde and #REGhl",
    'EC0000': "CALL #R0 if the parity/overflow flag is set (parity even)",
    'EE00': "Set the zero flag if #REGa=0, and reset the carry flag",
    'EF': "CALL #R40",
    'F0': "Return if the sign flag is not set (positive)",
    'F1': "Pop last item from stack into #REGaf",
    'F20000': "Jump to #R0 if the sign flag is not set (positive)",
    'F3': "Disable interrupts",
    'F40000': "CALL #R0 if the sign flag is not set (positive)",
    'F5': "Push #REGaf onto the stack",
    'F600': "Set the zero flag if #REGa=0, and reset the carry flag",
    'F7': "CALL #R48",
    'F8': "Return if the sign flag is set (negative)",
    'F9': "#REGsp=#REGhl",
    'FA0000': "Jump to #R0 if the sign flag is set (negative)",
    'FB': "Enable interrupts",
    'FC0000': "CALL #R0 if the sign flag is set (negative)",
    'FE00': "Set the zero flag if #REGa=0, and reset the carry flag",
    'FF': "CALL #R56",
    'CB00': RLC.format('#REGb'),
    'CB01': RLC.format('#REGc'),
    'CB02': RLC.format('#REGd'),
    'CB03': RLC.format('#REGe'),
    'CB04': RLC.format('#REGh'),
    'CB05': RLC.format('#REGl'),
    'CB06': RLC.format('(#REGhl)'),
    'CB07': RLC.format('#REGa'),
    'CB08': RRC.format('#REGb'),
    'CB09': RRC.format('#REGc'),
    'CB0A': RRC.format('#REGd'),
    'CB0B': RRC.format('#REGe'),
    'CB0C': RRC.format('#REGh'),
    'CB0D': RRC.format('#REGl'),
    'CB0E': RRC.format('(#REGhl)'),
    'CB0F': RRC.format('#REGa'),
    'CB10': RL.format('#REGb'),
    'CB11': RL.format('#REGc'),
    'CB12': RL.format('#REGd'),
    'CB13': RL.format('#REGe'),
    'CB14': RL.format('#REGh'),
    'CB15': RL.format('#REGl'),
    'CB16': RL.format('(#REGhl)'),
    'CB17': RL.format('#REGa'),
    'CB18': RR.format('#REGb'),
    'CB19': RR.format('#REGc'),
    'CB1A': RR.format('#REGd'),
    'CB1B': RR.format('#REGe'),
    'CB1C': RR.format('#REGh'),
    'CB1D': RR.format('#REGl'),
    'CB1E': RR.format('(#REGhl)'),
    'CB1F': RR.format('#REGa'),
    'CB20': SLA.format('#REGb'),
    'CB21': SLA.format('#REGc'),
    'CB22': SLA.format('#REGd'),
    'CB23': SLA.format('#REGe'),
    'CB24': SLA.format('#REGh'),
    'CB25': SLA.format('#REGl'),
    'CB26': SLA.format('(#REGhl)'),
    'CB27': SLA.format('#REGa'),
    'CB28': SRA.format('#REGb'),
    'CB29': SRA.format('#REGc'),
    'CB2A': SRA.format('#REGd'),
    'CB2B': SRA.format('#REGe'),
    'CB2C': SRA.format('#REGh'),
    'CB2D': SRA.format('#REGl'),
    'CB2E': SRA.format('(#REGhl)'),
    'CB2F': SRA.format('#REGa'),
    'CB30': SLL.format('#REGb'),
    'CB31': SLL.format('#REGc'),
    'CB32': SLL.format('#REGd'),
    'CB33': SLL.format('#REGe'),
    'CB34': SLL.format('#REGh'),
    'CB35': SLL.format('#REGl'),
    'CB36': SLL.format('(#REGhl)'),
    'CB37': SLL.format('#REGa'),
    'CB38': SRL.format('#REGb'),
    'CB39': SRL.format('#REGc'),
    'CB3A': SRL.format('#REGd'),
    'CB3B': SRL.format('#REGe'),
    'CB3C': SRL.format('#REGh'),
    'CB3D': SRL.format('#REGl'),
    'CB3E': SRL.format('(#REGhl)'),
    'CB3F': SRL.format('#REGa'),
    'CB40': BIT.format(0, '#REGb'),
    'CB41': BIT.format(0, '#REGc'),
    'CB42': BIT.format(0, '#REGd'),
    'CB43': BIT.format(0, '#REGe'),
    'CB44': BIT.format(0, '#REGh'),
    'CB45': BIT.format(0, '#REGl'),
    'CB46': BIT.format(0, '(#REGhl)'),
    'CB47': BIT.format(0, '#REGa'),
    'CB48': BIT.format(1, '#REGb'),
    'CB49': BIT.format(1, '#REGc'),
    'CB4A': BIT.format(1, '#REGd'),
    'CB4B': BIT.format(1, '#REGe'),
    'CB4C': BIT.format(1, '#REGh'),
    'CB4D': BIT.format(1, '#REGl'),
    'CB4E': BIT.format(1, '(#REGhl)'),
    'CB4F': BIT.format(1, '#REGa'),
    'CB50': BIT.format(2, '#REGb'),
    'CB51': BIT.format(2, '#REGc'),
    'CB52': BIT.format(2, '#REGd'),
    'CB53': BIT.format(2, '#REGe'),
    'CB54': BIT.format(2, '#REGh'),
    'CB55': BIT.format(2, '#REGl'),
    'CB56': BIT.format(2, '(#REGhl)'),
    'CB57': BIT.format(2, '#REGa'),
    'CB58': BIT.format(3, '#REGb'),
    'CB59': BIT.format(3, '#REGc'),
    'CB5A': BIT.format(3, '#REGd'),
    'CB5B': BIT.format(3, '#REGe'),
    'CB5C': BIT.format(3, '#REGh'),
    'CB5D': BIT.format(3, '#REGl'),
    'CB5E': BIT.format(3, '(#REGhl)'),
    'CB5F': BIT.format(3, '#REGa'),
    'CB60': BIT.format(4, '#REGb'),
    'CB61': BIT.format(4, '#REGc'),
    'CB62': BIT.format(4, '#REGd'),
    'CB63': BIT.format(4, '#REGe'),
    'CB64': BIT.format(4, '#REGh'),
    'CB65': BIT.format(4, '#REGl'),
    'CB66': BIT.format(4, '(#REGhl)'),
    'CB67': BIT.format(4, '#REGa'),
    'CB68': BIT.format(5, '#REGb'),
    'CB69': BIT.format(5, '#REGc'),
    'CB6A': BIT.format(5, '#REGd'),
    'CB6B': BIT.format(5, '#REGe'),
    'CB6C': BIT.format(5, '#REGh'),
    'CB6D': BIT.format(5, '#REGl'),
    'CB6E': BIT.format(5, '(#REGhl)'),
    'CB6F': BIT.format(5, '#REGa'),
    'CB70': BIT.format(6, '#REGb'),
    'CB71': BIT.format(6, '#REGc'),
    'CB72': BIT.format(6, '#REGd'),
    'CB73': BIT.format(6, '#REGe'),
    'CB74': BIT.format(6, '#REGh'),
    'CB75': BIT.format(6, '#REGl'),
    'CB76': BIT.format(6, '(#REGhl)'),
    'CB77': BIT.format(6, '#REGa'),
    'CB78': BIT.format(7, '#REGb'),
    'CB79': BIT.format(7, '#REGc'),
    'CB7A': BIT.format(7, '#REGd'),
    'CB7B': BIT.format(7, '#REGe'),
    'CB7C': BIT.format(7, '#REGh'),
    'CB7D': BIT.format(7, '#REGl'),
    'CB7E': BIT.format(7, '(#REGhl)'),
    'CB7F': BIT.format(7, '#REGa'),
    'CB80': RES.format(0, '#REGb'),
    'CB81': RES.format(0, '#REGc'),
    'CB82': RES.format(0, '#REGd'),
    'CB83': RES.format(0, '#REGe'),
    'CB84': RES.format(0, '#REGh'),
    'CB85': RES.format(0, '#REGl'),
    'CB86': RES.format(0, '(#REGhl)'),
    'CB87': RES.format(0, '#REGa'),
    'CB88': RES.format(1, '#REGb'),
    'CB89': RES.format(1, '#REGc'),
    'CB8A': RES.format(1, '#REGd'),
    'CB8B': RES.format(1, '#REGe'),
    'CB8C': RES.format(1, '#REGh'),
    'CB8D': RES.format(1, '#REGl'),
    'CB8E': RES.format(1, '(#REGhl)'),
    'CB8F': RES.format(1, '#REGa'),
    'CB90': RES.format(2, '#REGb'),
    'CB91': RES.format(2, '#REGc'),
    'CB92': RES.format(2, '#REGd'),
    'CB93': RES.format(2, '#REGe'),
    'CB94': RES.format(2, '#REGh'),
    'CB95': RES.format(2, '#REGl'),
    'CB96': RES.format(2, '(#REGhl)'),
    'CB97': RES.format(2, '#REGa'),
    'CB98': RES.format(3, '#REGb'),
    'CB99': RES.format(3, '#REGc'),
    'CB9A': RES.format(3, '#REGd'),
    'CB9B': RES.format(3, '#REGe'),
    'CB9C': RES.format(3, '#REGh'),
    'CB9D': RES.format(3, '#REGl'),
    'CB9E': RES.format(3, '(#REGhl)'),
    'CB9F': RES.format(3, '#REGa'),
    'CBA0': RES.format(4, '#REGb'),
    'CBA1': RES.format(4, '#REGc'),
    'CBA2': RES.format(4, '#REGd'),
    'CBA3': RES.format(4, '#REGe'),
    'CBA4': RES.format(4, '#REGh'),
    'CBA5': RES.format(4, '#REGl'),
    'CBA6': RES.format(4, '(#REGhl)'),
    'CBA7': RES.format(4, '#REGa'),
    'CBA8': RES.format(5, '#REGb'),
    'CBA9': RES.format(5, '#REGc'),
    'CBAA': RES.format(5, '#REGd'),
    'CBAB': RES.format(5, '#REGe'),
    'CBAC': RES.format(5, '#REGh'),
    'CBAD': RES.format(5, '#REGl'),
    'CBAE': RES.format(5, '(#REGhl)'),
    'CBAF': RES.format(5, '#REGa'),
    'CBB0': RES.format(6, '#REGb'),
    'CBB1': RES.format(6, '#REGc'),
    'CBB2': RES.format(6, '#REGd'),
    'CBB3': RES.format(6, '#REGe'),
    'CBB4': RES.format(6, '#REGh'),
    'CBB5': RES.format(6, '#REGl'),
    'CBB6': RES.format(6, '(#REGhl)'),
    'CBB7': RES.format(6, '#REGa'),
    'CBB8': RES.format(7, '#REGb'),
    'CBB9': RES.format(7, '#REGc'),
    'CBBA': RES.format(7, '#REGd'),
    'CBBB': RES.format(7, '#REGe'),
    'CBBC': RES.format(7, '#REGh'),
    'CBBD': RES.format(7, '#REGl'),
    'CBBE': RES.format(7, '(#REGhl)'),
    'CBBF': RES.format(7, '#REGa'),
    'CBC0': SET.format(0, '#REGb'),
    'CBC1': SET.format(0, '#REGc'),
    'CBC2': SET.format(0, '#REGd'),
    'CBC3': SET.format(0, '#REGe'),
    'CBC4': SET.format(0, '#REGh'),
    'CBC5': SET.format(0, '#REGl'),
    'CBC6': SET.format(0, '(#REGhl)'),
    'CBC7': SET.format(0, '#REGa'),
    'CBC8': SET.format(1, '#REGb'),
    'CBC9': SET.format(1, '#REGc'),
    'CBCA': SET.format(1, '#REGd'),
    'CBCB': SET.format(1, '#REGe'),
    'CBCC': SET.format(1, '#REGh'),
    'CBCD': SET.format(1, '#REGl'),
    'CBCE': SET.format(1, '(#REGhl)'),
    'CBCF': SET.format(1, '#REGa'),
    'CBD0': SET.format(2, '#REGb'),
    'CBD1': SET.format(2, '#REGc'),
    'CBD2': SET.format(2, '#REGd'),
    'CBD3': SET.format(2, '#REGe'),
    'CBD4': SET.format(2, '#REGh'),
    'CBD5': SET.format(2, '#REGl'),
    'CBD6': SET.format(2, '(#REGhl)'),
    'CBD7': SET.format(2, '#REGa'),
    'CBD8': SET.format(3, '#REGb'),
    'CBD9': SET.format(3, '#REGc'),
    'CBDA': SET.format(3, '#REGd'),
    'CBDB': SET.format(3, '#REGe'),
    'CBDC': SET.format(3, '#REGh'),
    'CBDD': SET.format(3, '#REGl'),
    'CBDE': SET.format(3, '(#REGhl)'),
    'CBDF': SET.format(3, '#REGa'),
    'CBE0': SET.format(4, '#REGb'),
    'CBE1': SET.format(4, '#REGc'),
    'CBE2': SET.format(4, '#REGd'),
    'CBE3': SET.format(4, '#REGe'),
    'CBE4': SET.format(4, '#REGh'),
    'CBE5': SET.format(4, '#REGl'),
    'CBE6': SET.format(4, '(#REGhl)'),
    'CBE7': SET.format(4, '#REGa'),
    'CBE8': SET.format(5, '#REGb'),
    'CBE9': SET.format(5, '#REGc'),
    'CBEA': SET.format(5, '#REGd'),
    'CBEB': SET.format(5, '#REGe'),
    'CBEC': SET.format(5, '#REGh'),
    'CBED': SET.format(5, '#REGl'),
    'CBEE': SET.format(5, '(#REGhl)'),
    'CBEF': SET.format(5, '#REGa'),
    'CBF0': SET.format(6, '#REGb'),
    'CBF1': SET.format(6, '#REGc'),
    'CBF2': SET.format(6, '#REGd'),
    'CBF3': SET.format(6, '#REGe'),
    'CBF4': SET.format(6, '#REGh'),
    'CBF5': SET.format(6, '#REGl'),
    'CBF6': SET.format(6, '(#REGhl)'),
    'CBF7': SET.format(6, '#REGa'),
    'CBF8': SET.format(7, '#REGb'),
    'CBF9': SET.format(7, '#REGc'),
    'CBFA': SET.format(7, '#REGd'),
    'CBFB': SET.format(7, '#REGe'),
    'CBFC': SET.format(7, '#REGh'),
    'CBFD': SET.format(7, '#REGl'),
    'CBFE': SET.format(7, '(#REGhl)'),
    'CBFF': SET.format(7, '#REGa'),
    'ED40': "#REGb=IN #REGbc",
    'ED41': "OUT #REGbc,#REGb",
    'ED42': "#REGhl=#REGhl-carry-#REGbc",
    'ED43FFFF': "POKE #N(65535,4,,1)($),#REGc; POKE #N(0,4,,1)($),#REGb",
    'ED44': "#REGa=#N(256,2,,1)($)-#REGa",
    'ED45': "Return from non-maskable interrupt",
    'ED46': "Set interrupt mode 0",
    'ED47': "#REGi=#REGa",
    'ED48': "#REGc=IN #REGbc",
    'ED49': "OUT #REGbc,#REGc",
    'ED4A': "#REGhl=#REGhl+carry+#REGbc",
    'ED4B0000': "#REGc=PEEK #N(0,4,,1)($); #REGb=PEEK #N(1,4,,1)($)",
    'ED4C': "#REGa=#N(256,2,,1)($)-#REGa",
    'ED4D': "Return from maskable interrupt",
    'ED4E': "Set interrupt mode 0",
    'ED4F': "#REGr=#REGa",
    'ED50': "#REGd=IN #REGbc",
    'ED51': "OUT #REGbc,#REGd",
    'ED52': "#REGhl=#REGhl-carry-#REGde",
    'ED530000': "POKE #N(0,4,,1)($),#REGe; POKE #N(1,4,,1)($),#REGd",
    'ED54': "#REGa=#N(256,2,,1)($)-#REGa",
    'ED55': "Return from non-maskable interrupt",
    'ED56': "Set interrupt mode 1",
    'ED57': "#REGa=#REGi",
    'ED58': "#REGe=IN #REGbc",
    'ED59': "OUT #REGbc,#REGe",
    'ED5A': "#REGhl=#REGhl+carry+#REGde",
    'ED5BFFFF': "#REGe=PEEK #N(65535,4,,1)($); #REGd=PEEK #N(0,4,,1)($)",
    'ED5C': "#REGa=#N(256,2,,1)($)-#REGa",
    'ED5D': "Return from non-maskable interrupt",
    'ED5E': "Set interrupt mode 2",
    'ED5F': "#REGa=#REGr",
    'ED60': "#REGh=IN #REGbc",
    'ED61': "OUT #REGbc,#REGh",
    'ED62': "#REGhl=#N($FFFF,4,,1)($) if carry flag is set, 0 otherwise",
    'ED63FFFF': "POKE #N(65535,4,,1)($),#REGl; POKE #N(0,4,,1)($),#REGh",
    'ED64': "#REGa=#N(256,2,,1)($)-#REGa",
    'ED65': "Return from non-maskable interrupt",
    'ED66': "Set interrupt mode 0",
    'ED67': "Rotate the low nibble of #REGa and all of (#REGhl) right 4 bits",
    'ED68': "#REGl=IN #REGbc",
    'ED69': "OUT #REGbc,#REGl",
    'ED6A': "#REGhl=#REGhl+carry+#REGhl",
    'ED6B0000': "#REGl=PEEK #N(0,4,,1)($); #REGh=PEEK #N(1,4,,1)($)",
    'ED6C': "#REGa=#N(256,2,,1)($)-#REGa",
    'ED6D': "Return from non-maskable interrupt",
    'ED6E': "Set interrupt mode 0",
    'ED6F': "Rotate the low nibble of #REGa and all of (#REGhl) left 4 bits",
    'ED70': "Read from port #REGbc and set flags accordingly",
    'ED71': "OUT #REGbc,0",
    'ED72': "#REGhl=#REGhl-carry-#REGsp",
    'ED730000': "POKE #N(0,4,,1)($),#REGsp-lo; POKE #N(1,4,,1)($),#REGsp-hi",
    'ED74': "#REGa=#N(256,2,,1)($)-#REGa",
    'ED75': "Return from non-maskable interrupt",
    'ED76': "Set interrupt mode 1",
    'ED78': "#REGa=IN #REGbc",
    'ED79': "OUT #REGbc,#REGa",
    'ED7A': "#REGhl=#REGhl+carry+#REGsp",
    'ED7BFFFF': "#REGsp=PEEK #N(65535,4,,1)($)+#N(256,2,,1)($)*PEEK #N(0,4,,1)($)",
    'ED7C': "#REGa=#N(256,2,,1)($)-#REGa",
    'ED7D': "Return from non-maskable interrupt",
    'ED7E': "Set interrupt mode 2",
    'EDA0': "POKE #REGde,PEEK #REGhl; #REGhl=#REGhl+1; #REGde=#REGde+1; #REGbc=#REGbc-1",
    'EDA1': "Compare #REGa with PEEK #REGhl; #REGhl=#REGhl+1; #REGbc=#REGbc-1",
    'EDA2': "POKE #REGhl,IN #REGbc; #REGhl=#REGhl+1; #REGb=#REGb-1",
    'EDA3': "#REGb=#REGb-1; OUT #REGbc,PEEK #REGhl; #REGhl=#REGhl+1",
    'EDA8': "POKE #REGde,PEEK #REGhl; #REGhl=#REGhl-1; #REGde=#REGde-1; #REGbc=#REGbc-1",
    'EDA9': "Compare #REGa with PEEK #REGhl; #REGhl=#REGhl-1; #REGbc=#REGbc-1",
    'EDAA': "POKE #REGhl,IN #REGbc; #REGhl=#REGhl-1; #REGb=#REGb-1",
    'EDAB': "#REGb=#REGb-1; OUT #REGbc,PEEK #REGhl; #REGhl=#REGhl-1",
    'EDB0': "POKE #REGde,PEEK #REGhl; #REGhl=#REGhl+1; #REGde=#REGde+1; #REGbc=#REGbc-1; repeat until #REGbc=0",
    'EDB1': "Compare #REGa with PEEK #REGhl; #REGhl=#REGhl+1; #REGbc=#REGbc-1; repeat until #REGbc=0 or #REGa=PEEK #REGhl",
    'EDB2': "POKE #REGhl,IN #REGbc; #REGhl=#REGhl+1; #REGb=#REGb-1; repeat until #REGb=0",
    'EDB3': "#REGb=#REGb-1; OUT #REGbc,PEEK #REGhl; #REGhl=#REGhl+1; repeat until #REGb=0",
    'EDB8': "POKE #REGde,PEEK #REGhl; #REGhl=#REGhl-1; #REGde=#REGde-1; #REGbc=#REGbc-1; repeat until #REGbc=0",
    'EDB9': "Compare #REGa with PEEK #REGhl; #REGhl=#REGhl-1; #REGbc=#REGbc-1; repeat until #REGbc=0 or #REGa=PEEK #REGhl",
    'EDBA': "POKE #REGhl,IN #REGbc; #REGhl=#REGhl-1; #REGb=#REGb-1; repeat until #REGb=0",
    'EDBB': "#REGb=#REGb-1; OUT #REGbc,PEEK #REGhl; #REGhl=#REGhl-1; repeat until #REGb=0",
}

AFTER_DD = {
    'DD09': "#REGix=#REGix+#REGbc",
    'DD19': "#REGix=#REGix+#REGde",
    'DD210100': "#REGix=#N(1,4,,1)($)",
    'DD22FF00': "POKE #N(255,4,,1)($),#REGixl; POKE #N(256,4,,1)($),#REGixh",
    'DD23': "#REGix=#REGix+1",
    'DD24': "#REGixh=#REGixh+1",
    'DD25': "#REGixh=#REGixh-1",
    'DD26FF': "#REGixh=#N(255,2,,1)($)",
    'DD29': "#REGix=#REGix+#REGix",
    'DD2AFF00': "#REGixl=PEEK #N(255,4,,1)($); #REGixh=PEEK #N(256,4,,1)($)",
    'DD2B': "#REGix=#REGix-1",
    'DD2C': "#REGixl=#REGixl+1",
    'DD2D': "#REGixl=#REGixl-1",
    'DD2EFF': "#REGixl=#N(255,2,,1)($)",
    'DD34FF': f"POKE {IX_FF},(PEEK {IX_FF})+1",
    'DD3501': f"POKE {IX_01},(PEEK {IX_01})-1",
    'DD36FF00': f"POKE {IX_FF},0",
    'DD39': "#REGix=#REGix+#REGsp",
    'DD44': "#REGb=#REGixh",
    'DD45': "#REGb=#REGixl",
    'DD46FF': f"#REGb=PEEK {IX_FF}",
    'DD4C': "#REGc=#REGixh",
    'DD4D': "#REGc=#REGixl",
    'DD4EFF': f"#REGc=PEEK {IX_FF}",
    'DD54': "#REGd=#REGixh",
    'DD55': "#REGd=#REGixl",
    'DD56FF': f"#REGd=PEEK {IX_FF}",
    'DD5C': "#REGe=#REGixh",
    'DD5D': "#REGe=#REGixl",
    'DD5EFF': f"#REGe=PEEK {IX_FF}",
    'DD60': "#REGixh=#REGb",
    'DD61': "#REGixh=#REGc",
    'DD62': "#REGixh=#REGd",
    'DD63': "#REGixh=#REGe",
    'DD64': "Do nothing",
    'DD65': "#REGixh=#REGixl",
    'DD66FF': f"#REGh=PEEK {IX_FF}",
    'DD67': "#REGixh=#REGa",
    'DD68': "#REGixl=#REGb",
    'DD69': "#REGixl=#REGc",
    'DD6A': "#REGixl=#REGd",
    'DD6B': "#REGixl=#REGe",
    'DD6C': "#REGixl=#REGixh",
    'DD6D': "Do nothing",
    'DD6EFF': f"#REGl=PEEK {IX_FF}",
    'DD6F': "#REGixl=#REGa",
    'DD70FF': f"POKE {IX_FF},#REGb",
    'DD7101': f"POKE {IX_01},#REGc",
    'DD72FF': f"POKE {IX_FF},#REGd",
    'DD7301': f"POKE {IX_01},#REGe",
    'DD74FF': f"POKE {IX_FF},#REGh",
    'DD7501': f"POKE {IX_01},#REGl",
    'DD7701': f"POKE {IX_01},#REGa",
    'DD7C': "#REGa=#REGixh",
    'DD7D': "#REGa=#REGixl",
    'DD7EFF': f"#REGa=PEEK {IX_FF}",
    'DD84': "#REGa=#REGa+#REGixh",
    'DD85': "#REGa=#REGa+#REGixl",
    'DD86FF': f"#REGa=#REGa+PEEK {IX_FF}",
    'DD8C': "#REGa=#REGa+carry+#REGixh",
    'DD8D': "#REGa=#REGa+carry+#REGixl",
    'DD8EFF': f"#REGa=#REGa+carry+PEEK {IX_FF}",
    'DD94': "#REGa=#REGa-#REGixh",
    'DD95': "#REGa=#REGa-#REGixl",
    'DD96FF': f"#REGa=#REGa-PEEK {IX_FF}",
    'DD9C': "#REGa=#REGa-carry-#REGixh",
    'DD9D': "#REGa=#REGa-carry-#REGixl",
    'DD9EFF': f"#REGa=#REGa-carry-PEEK {IX_FF}",
    'DDA4': "#REGa=#REGa&#REGixh",
    'DDA5': "#REGa=#REGa&#REGixl",
    'DDA6FF': f"#REGa=#REGa&PEEK {IX_FF}",
    'DDAC': "#REGa=#REGa^#REGixh",
    'DDAD': "#REGa=#REGa^#REGixl",
    'DDAEFF': f"#REGa=#REGa^PEEK {IX_FF}",
    'DDB4': "#REGa=#REGa|#REGixh",
    'DDB5': "#REGa=#REGa|#REGixl",
    'DDB6FF': f"#REGa=#REGa|PEEK {IX_FF}",
    'DDBC': "Set the zero flag if #REGa=#REGixh, or the carry flag if #REGa<#REGixh",
    'DDBD': "Set the zero flag if #REGa=#REGixl, or the carry flag if #REGa<#REGixl",
    'DDBEFF': f"Set the zero flag if #REGa=PEEK {IX_FF}, or the carry flag if #REGa<PEEK {IX_FF}",
    'DDE1': "Pop last item from stack into #REGix",
    'DDE3': "Exchange the last item on the stack with #REGix",
    'DDE5': "Push #REGix onto the stack",
    'DDE9': "Jump to #REGix",
    'DDF9': "#REGsp=#REGix",
    'DDCBFF00': RLC_r.format(IX_FF, 'b'),
    'DDCB0101': RLC_r.format(IX_01, 'c'),
    'DDCBFF02': RLC_r.format(IX_FF, 'd'),
    'DDCB0103': RLC_r.format(IX_01, 'e'),
    'DDCBFF04': RLC_r.format(IX_FF, 'h'),
    'DDCB0105': RLC_r.format(IX_01, 'l'),
    'DDCBFF06': RLC.format(IX_FF),
    'DDCB0107': RLC_r.format(IX_01, 'a'),
    'DDCBFF08': RRC_r.format(IX_FF, 'b'),
    'DDCB0109': RRC_r.format(IX_01, 'c'),
    'DDCBFF0A': RRC_r.format(IX_FF, 'd'),
    'DDCB010B': RRC_r.format(IX_01, 'e'),
    'DDCBFF0C': RRC_r.format(IX_FF, 'h'),
    'DDCB010D': RRC_r.format(IX_01, 'l'),
    'DDCBFF0E': RRC.format(IX_FF),
    'DDCB010F': RRC_r.format(IX_01, 'a'),
    'DDCBFF10': RL_r.format(IX_FF, 'b'),
    'DDCB0111': RL_r.format(IX_01, 'c'),
    'DDCBFF12': RL_r.format(IX_FF, 'd'),
    'DDCB0113': RL_r.format(IX_01, 'e'),
    'DDCBFF14': RL_r.format(IX_FF, 'h'),
    'DDCB0115': RL_r.format(IX_01, 'l'),
    'DDCBFF16': RL.format(IX_FF),
    'DDCB0117': RL_r.format(IX_01, 'a'),
    'DDCBFF18': RR_r.format(IX_FF, 'b'),
    'DDCB0119': RR_r.format(IX_01, 'c'),
    'DDCBFF1A': RR_r.format(IX_FF, 'd'),
    'DDCB011B': RR_r.format(IX_01, 'e'),
    'DDCBFF1C': RR_r.format(IX_FF, 'h'),
    'DDCB011D': RR_r.format(IX_01, 'l'),
    'DDCBFF1E': RR.format(IX_FF),
    'DDCB011F': RR_r.format(IX_01, 'a'),
    'DDCBFF20': SLA_r.format(IX_FF, 'b'),
    'DDCB0121': SLA_r.format(IX_01, 'c'),
    'DDCBFF22': SLA_r.format(IX_FF, 'd'),
    'DDCB0123': SLA_r.format(IX_01, 'e'),
    'DDCBFF24': SLA_r.format(IX_FF, 'h'),
    'DDCB0125': SLA_r.format(IX_01, 'l'),
    'DDCBFF26': SLA.format(IX_FF),
    'DDCB0127': SLA_r.format(IX_01, 'a'),
    'DDCBFF28': SRA_r.format(IX_FF, 'b'),
    'DDCB0129': SRA_r.format(IX_01, 'c'),
    'DDCBFF2A': SRA_r.format(IX_FF, 'd'),
    'DDCB012B': SRA_r.format(IX_01, 'e'),
    'DDCBFF2C': SRA_r.format(IX_FF, 'h'),
    'DDCB012D': SRA_r.format(IX_01, 'l'),
    'DDCBFF2E': SRA.format(IX_FF),
    'DDCB012F': SRA_r.format(IX_01, 'a'),
    'DDCBFF30': SLL_r.format(IX_FF, 'b'),
    'DDCB0131': SLL_r.format(IX_01, 'c'),
    'DDCBFF32': SLL_r.format(IX_FF, 'd'),
    'DDCB0133': SLL_r.format(IX_01, 'e'),
    'DDCBFF34': SLL_r.format(IX_FF, 'h'),
    'DDCB0135': SLL_r.format(IX_01, 'l'),
    'DDCBFF36': SLL.format(IX_FF),
    'DDCB0137': SLL_r.format(IX_01, 'a'),
    'DDCBFF38': SRL_r.format(IX_FF, 'b'),
    'DDCB0139': SRL_r.format(IX_01, 'c'),
    'DDCBFF3A': SRL_r.format(IX_FF, 'd'),
    'DDCB013B': SRL_r.format(IX_01, 'e'),
    'DDCBFF3C': SRL_r.format(IX_FF, 'h'),
    'DDCB013D': SRL_r.format(IX_01, 'l'),
    'DDCBFF3E': SRL.format(IX_FF),
    'DDCB013F': SRL_r.format(IX_01, 'a'),
    'DDCBFF40': BIT.format(0, IX_FF),
    'DDCB0141': BIT.format(0, IX_01),
    'DDCBFF42': BIT.format(0, IX_FF),
    'DDCB0143': BIT.format(0, IX_01),
    'DDCBFF44': BIT.format(0, IX_FF),
    'DDCB0145': BIT.format(0, IX_01),
    'DDCBFF46': BIT.format(0, IX_FF),
    'DDCB0147': BIT.format(0, IX_01),
    'DDCBFF48': BIT.format(1, IX_FF),
    'DDCB0149': BIT.format(1, IX_01),
    'DDCBFF4A': BIT.format(1, IX_FF),
    'DDCB014B': BIT.format(1, IX_01),
    'DDCBFF4C': BIT.format(1, IX_FF),
    'DDCB014D': BIT.format(1, IX_01),
    'DDCBFF4E': BIT.format(1, IX_FF),
    'DDCB014F': BIT.format(1, IX_01),
    'DDCBFF50': BIT.format(2, IX_FF),
    'DDCB0151': BIT.format(2, IX_01),
    'DDCBFF52': BIT.format(2, IX_FF),
    'DDCB0153': BIT.format(2, IX_01),
    'DDCBFF54': BIT.format(2, IX_FF),
    'DDCB0155': BIT.format(2, IX_01),
    'DDCBFF56': BIT.format(2, IX_FF),
    'DDCB0157': BIT.format(2, IX_01),
    'DDCBFF58': BIT.format(3, IX_FF),
    'DDCB0159': BIT.format(3, IX_01),
    'DDCBFF5A': BIT.format(3, IX_FF),
    'DDCB015B': BIT.format(3, IX_01),
    'DDCBFF5C': BIT.format(3, IX_FF),
    'DDCB015D': BIT.format(3, IX_01),
    'DDCBFF5E': BIT.format(3, IX_FF),
    'DDCB015F': BIT.format(3, IX_01),
    'DDCBFF60': BIT.format(4, IX_FF),
    'DDCB0161': BIT.format(4, IX_01),
    'DDCBFF62': BIT.format(4, IX_FF),
    'DDCB0163': BIT.format(4, IX_01),
    'DDCBFF64': BIT.format(4, IX_FF),
    'DDCB0165': BIT.format(4, IX_01),
    'DDCBFF66': BIT.format(4, IX_FF),
    'DDCB0167': BIT.format(4, IX_01),
    'DDCBFF68': BIT.format(5, IX_FF),
    'DDCB0169': BIT.format(5, IX_01),
    'DDCBFF6A': BIT.format(5, IX_FF),
    'DDCB016B': BIT.format(5, IX_01),
    'DDCBFF6C': BIT.format(5, IX_FF),
    'DDCB016D': BIT.format(5, IX_01),
    'DDCBFF6E': BIT.format(5, IX_FF),
    'DDCB016F': BIT.format(5, IX_01),
    'DDCBFF70': BIT.format(6, IX_FF),
    'DDCB0171': BIT.format(6, IX_01),
    'DDCBFF72': BIT.format(6, IX_FF),
    'DDCB0173': BIT.format(6, IX_01),
    'DDCBFF74': BIT.format(6, IX_FF),
    'DDCB0175': BIT.format(6, IX_01),
    'DDCBFF76': BIT.format(6, IX_FF),
    'DDCB0177': BIT.format(6, IX_01),
    'DDCBFF78': BIT.format(7, IX_FF),
    'DDCB0179': BIT.format(7, IX_01),
    'DDCBFF7A': BIT.format(7, IX_FF),
    'DDCB017B': BIT.format(7, IX_01),
    'DDCBFF7C': BIT.format(7, IX_FF),
    'DDCB017D': BIT.format(7, IX_01),
    'DDCBFF7E': BIT.format(7, IX_FF),
    'DDCB017F': BIT.format(7, IX_01),
    'DDCBFF80': RES_r.format(0, IX_FF, 'b'),
    'DDCB0181': RES_r.format(0, IX_01, 'c'),
    'DDCBFF82': RES_r.format(0, IX_FF, 'd'),
    'DDCB0183': RES_r.format(0, IX_01, 'e'),
    'DDCBFF84': RES_r.format(0, IX_FF, 'h'),
    'DDCB0185': RES_r.format(0, IX_01, 'l'),
    'DDCBFF86': RES.format(0, IX_FF),
    'DDCB0187': RES_r.format(0, IX_01, 'a'),
    'DDCBFF88': RES_r.format(1, IX_FF, 'b'),
    'DDCB0189': RES_r.format(1, IX_01, 'c'),
    'DDCBFF8A': RES_r.format(1, IX_FF, 'd'),
    'DDCB018B': RES_r.format(1, IX_01, 'e'),
    'DDCBFF8C': RES_r.format(1, IX_FF, 'h'),
    'DDCB018D': RES_r.format(1, IX_01, 'l'),
    'DDCBFF8E': RES.format(1, IX_FF),
    'DDCB018F': RES_r.format(1, IX_01, 'a'),
    'DDCBFF90': RES_r.format(2, IX_FF, 'b'),
    'DDCB0191': RES_r.format(2, IX_01, 'c'),
    'DDCBFF92': RES_r.format(2, IX_FF, 'd'),
    'DDCB0193': RES_r.format(2, IX_01, 'e'),
    'DDCBFF94': RES_r.format(2, IX_FF, 'h'),
    'DDCB0195': RES_r.format(2, IX_01, 'l'),
    'DDCBFF96': RES.format(2, IX_FF),
    'DDCB0197': RES_r.format(2, IX_01, 'a'),
    'DDCBFF98': RES_r.format(3, IX_FF, 'b'),
    'DDCB0199': RES_r.format(3, IX_01, 'c'),
    'DDCBFF9A': RES_r.format(3, IX_FF, 'd'),
    'DDCB019B': RES_r.format(3, IX_01, 'e'),
    'DDCBFF9C': RES_r.format(3, IX_FF, 'h'),
    'DDCB019D': RES_r.format(3, IX_01, 'l'),
    'DDCBFF9E': RES.format(3, IX_FF),
    'DDCB019F': RES_r.format(3, IX_01, 'a'),
    'DDCBFFA0': RES_r.format(4, IX_FF, 'b'),
    'DDCB01A1': RES_r.format(4, IX_01, 'c'),
    'DDCBFFA2': RES_r.format(4, IX_FF, 'd'),
    'DDCB01A3': RES_r.format(4, IX_01, 'e'),
    'DDCBFFA4': RES_r.format(4, IX_FF, 'h'),
    'DDCB01A5': RES_r.format(4, IX_01, 'l'),
    'DDCBFFA6': RES.format(4, IX_FF),
    'DDCB01A7': RES_r.format(4, IX_01, 'a'),
    'DDCBFFA8': RES_r.format(5, IX_FF, 'b'),
    'DDCB01A9': RES_r.format(5, IX_01, 'c'),
    'DDCBFFAA': RES_r.format(5, IX_FF, 'd'),
    'DDCB01AB': RES_r.format(5, IX_01, 'e'),
    'DDCBFFAC': RES_r.format(5, IX_FF, 'h'),
    'DDCB01AD': RES_r.format(5, IX_01, 'l'),
    'DDCBFFAE': RES.format(5, IX_FF),
    'DDCB01AF': RES_r.format(5, IX_01, 'a'),
    'DDCBFFB0': RES_r.format(6, IX_FF, 'b'),
    'DDCB01B1': RES_r.format(6, IX_01, 'c'),
    'DDCBFFB2': RES_r.format(6, IX_FF, 'd'),
    'DDCB01B3': RES_r.format(6, IX_01, 'e'),
    'DDCBFFB4': RES_r.format(6, IX_FF, 'h'),
    'DDCB01B5': RES_r.format(6, IX_01, 'l'),
    'DDCBFFB6': RES.format(6, IX_FF),
    'DDCB01B7': RES_r.format(6, IX_01, 'a'),
    'DDCBFFB8': RES_r.format(7, IX_FF, 'b'),
    'DDCB01B9': RES_r.format(7, IX_01, 'c'),
    'DDCBFFBA': RES_r.format(7, IX_FF, 'd'),
    'DDCB01BB': RES_r.format(7, IX_01, 'e'),
    'DDCBFFBC': RES_r.format(7, IX_FF, 'h'),
    'DDCB01BD': RES_r.format(7, IX_01, 'l'),
    'DDCBFFBE': RES.format(7, IX_FF),
    'DDCB01BF': RES_r.format(7, IX_01, 'a'),
    'DDCBFFC0': SET_r.format(0, IX_FF, 'b'),
    'DDCB01C1': SET_r.format(0, IX_01, 'c'),
    'DDCBFFC2': SET_r.format(0, IX_FF, 'd'),
    'DDCB01C3': SET_r.format(0, IX_01, 'e'),
    'DDCBFFC4': SET_r.format(0, IX_FF, 'h'),
    'DDCB01C5': SET_r.format(0, IX_01, 'l'),
    'DDCBFFC6': SET.format(0, IX_FF),
    'DDCB01C7': SET_r.format(0, IX_01, 'a'),
    'DDCBFFC8': SET_r.format(1, IX_FF, 'b'),
    'DDCB01C9': SET_r.format(1, IX_01, 'c'),
    'DDCBFFCA': SET_r.format(1, IX_FF, 'd'),
    'DDCB01CB': SET_r.format(1, IX_01, 'e'),
    'DDCBFFCC': SET_r.format(1, IX_FF, 'h'),
    'DDCB01CD': SET_r.format(1, IX_01, 'l'),
    'DDCBFFCE': SET.format(1, IX_FF),
    'DDCB01CF': SET_r.format(1, IX_01, 'a'),
    'DDCBFFD0': SET_r.format(2, IX_FF, 'b'),
    'DDCB01D1': SET_r.format(2, IX_01, 'c'),
    'DDCBFFD2': SET_r.format(2, IX_FF, 'd'),
    'DDCB01D3': SET_r.format(2, IX_01, 'e'),
    'DDCBFFD4': SET_r.format(2, IX_FF, 'h'),
    'DDCB01D5': SET_r.format(2, IX_01, 'l'),
    'DDCBFFD6': SET.format(2, IX_FF),
    'DDCB01D7': SET_r.format(2, IX_01, 'a'),
    'DDCBFFD8': SET_r.format(3, IX_FF, 'b'),
    'DDCB01D9': SET_r.format(3, IX_01, 'c'),
    'DDCBFFDA': SET_r.format(3, IX_FF, 'd'),
    'DDCB01DB': SET_r.format(3, IX_01, 'e'),
    'DDCBFFDC': SET_r.format(3, IX_FF, 'h'),
    'DDCB01DD': SET_r.format(3, IX_01, 'l'),
    'DDCBFFDE': SET.format(3, IX_FF),
    'DDCB01DF': SET_r.format(3, IX_01, 'a'),
    'DDCBFFE0': SET_r.format(4, IX_FF, 'b'),
    'DDCB01E1': SET_r.format(4, IX_01, 'c'),
    'DDCBFFE2': SET_r.format(4, IX_FF, 'd'),
    'DDCB01E3': SET_r.format(4, IX_01, 'e'),
    'DDCBFFE4': SET_r.format(4, IX_FF, 'h'),
    'DDCB01E5': SET_r.format(4, IX_01, 'l'),
    'DDCBFFE6': SET.format(4, IX_FF),
    'DDCB01E7': SET_r.format(4, IX_01, 'a'),
    'DDCBFFE8': SET_r.format(5, IX_FF, 'b'),
    'DDCB01E9': SET_r.format(5, IX_01, 'c'),
    'DDCBFFEA': SET_r.format(5, IX_FF, 'd'),
    'DDCB01EB': SET_r.format(5, IX_01, 'e'),
    'DDCBFFEC': SET_r.format(5, IX_FF, 'h'),
    'DDCB01ED': SET_r.format(5, IX_01, 'l'),
    'DDCBFFEE': SET.format(5, IX_FF),
    'DDCB01EF': SET_r.format(5, IX_01, 'a'),
    'DDCBFFF0': SET_r.format(6, IX_FF, 'b'),
    'DDCB01F1': SET_r.format(6, IX_01, 'c'),
    'DDCBFFF2': SET_r.format(6, IX_FF, 'd'),
    'DDCB01F3': SET_r.format(6, IX_01, 'e'),
    'DDCBFFF4': SET_r.format(6, IX_FF, 'h'),
    'DDCB01F5': SET_r.format(6, IX_01, 'l'),
    'DDCBFFF6': SET.format(6, IX_FF),
    'DDCB01F7': SET_r.format(6, IX_01, 'a'),
    'DDCBFFF8': SET_r.format(7, IX_FF, 'b'),
    'DDCB01F9': SET_r.format(7, IX_01, 'c'),
    'DDCBFFFA': SET_r.format(7, IX_FF, 'd'),
    'DDCB01FB': SET_r.format(7, IX_01, 'e'),
    'DDCBFFFC': SET_r.format(7, IX_FF, 'h'),
    'DDCB01FD': SET_r.format(7, IX_01, 'l'),
    'DDCBFFFE': SET.format(7, IX_FF),
    'DDCB01FF': SET_r.format(7, IX_01, 'a'),
}

CONDITIONALS = {
    'SF_NA': {
        'F0': 'Return if the sign flag is not set (positive)',          # RET P
        'F20000': 'Jump to #R0 if the sign flag is not set (positive)', # JP P,0
        'F40000': 'CALL #R0 if the sign flag is not set (positive)',    # CALL P,0
        'F8': 'Return if the sign flag is set (negative)',              # RET M
        'FA0000': 'Jump to #R0 if the sign flag is set (negative)',     # JP M,0
        'FC0000': 'CALL #R0 if the sign flag is set (negative)',        # CALL M,0
    },
    'SF_SIGN': {
        'F0': 'Return if {}<#N(128,2,,1)($)',           # RET P
        'F20000': 'Jump to #R0 if {}<#N(128,2,,1)($)',  # JP P,0
        'F40000': 'CALL #R0 if {}<#N(128,2,,1)($)',     # CALL P,0
        'F8': 'Return if {}>=#N(128,2,,1)($)',          # RET M
        'FA0000': 'Jump to #R0 if {}>=#N(128,2,,1)($)', # JP M,0
        'FC0000': 'CALL #R0 if {}>=#N(128,2,,1)($)',    # CALL M,0
    },
    'SF_BIT_7': {
        'F0': 'Return if {} is reset',          # RET P
        'F20000': 'Jump to #R0 if {} is reset', # JP P,0
        'F40000': 'CALL #R0 if {} is reset',    # CALL P,0
        'F8': 'Return if {} is set',            # RET M
        'FA0000': 'Jump to #R0 if {} is set',   # JP M,0
        'FC0000': 'CALL #R0 if {} is set',      # CALL M,0
    },
    'ZF_NA': {
        '2000': 'Jump to #R32770 if the zero flag is not set', # JR NZ,nn
        '2800': 'Jump to #R32770 if the zero flag is set',     # JR Z,nn
        'C0': 'Return if the zero flag is not set',            # RET NZ
        'C20000': 'Jump to #R0 if the zero flag is not set',   # JP NZ,0
        'C40000': 'CALL #R0 if the zero flag is not set',      # CALL NZ,0
        'C8': 'Return if the zero flag is set',                # RET Z
        'CA0000': 'Jump to #R0 if the zero flag is set',       # JP Z,0
        'CC0000': 'CALL #R0 if the zero flag is set',          # CALL Z,0
    },
    'ZF_ZERO': {
        '2000': 'Jump to #R32770 if {}>0', # JR NZ,nn
        '2800': 'Jump to #R32770 if {}=0', # JR Z,nn
        'C0': 'Return if {}>0',            # RET NZ
        'C20000': 'Jump to #R0 if {}>0',   # JP NZ,0
        'C40000': 'CALL #R0 if {}>0',      # CALL NZ,0
        'C8': 'Return if {}=0',            # RET Z
        'CA0000': 'Jump to #R0 if {}=0',   # JP Z,0
        'CC0000': 'CALL #R0 if {}=0',      # CALL Z,0
    },
    'ZF_COMPARE': {
        '2000': 'Jump to #R32770 if #REGa<>{}', # JR NZ,nn
        '2800': 'Jump to #R32770 if #REGa={}',  # JR Z,nn
        'C0': 'Return if #REGa<>{}',            # RET NZ
        'C20000': 'Jump to #R0 if #REGa<>{}',   # JP NZ,0
        'C40000': 'CALL #R0 if #REGa<>{}',      # CALL NZ,0
        'C8': 'Return if #REGa={}',             # RET Z
        'CA0000': 'Jump to #R0 if #REGa={}',    # JP Z,0
        'CC0000': 'CALL #R0 if #REGa={}',       # CALL Z,0
    },
    'ZF_BIT': {
        '2000': 'Jump to #R32770 if {} is set',   # JR NZ,nn
        '2800': 'Jump to #R32770 if {} is reset', # JR Z,nn
        'C0': 'Return if {} is set',              # RET NZ
        'C20000': 'Jump to #R0 if {} is set',     # JP NZ,0
        'C40000': 'CALL #R0 if {} is set',        # CALL NZ,0
        'C8': 'Return if {} is reset',            # RET Z
        'CA0000': 'Jump to #R0 if {} is reset',   # JP Z,0
        'CC0000': 'CALL #R0 if {} is reset',      # CALL Z,0
    },
    'PF_NA': {
        'E0': 'Return if the parity/overflow flag is not set (parity odd)',          # RET PO
        'E20000': 'Jump to #R0 if the parity/overflow flag is not set (parity odd)', # JP PO,0
        'E40000': 'CALL #R0 if the parity/overflow flag is not set (parity odd)',    # CALL PO,0
        'E8': 'Return if the parity/overflow flag is set (parity even)',             # RET PE
        'EA0000': 'Jump to #R0 if the parity/overflow flag is set (parity even)',    # JP PE,0
        'EC0000': 'CALL #R0 if the parity/overflow flag is set (parity even)',       # CALL PE,0
    },
    'PF_PARITY': {
        'E0': 'Return if the parity flag is not set',          # RET PO
        'E20000': 'Jump to #R0 if the parity flag is not set', # JP PO,0
        'E40000': 'CALL #R0 if the parity flag is not set',    # CALL PO,0
        'E8': 'Return if the parity flag is set',              # RET PE
        'EA0000': 'Jump to #R0 if the parity flag is set',     # JP PE,0
        'EC0000': 'CALL #R0 if the parity flag is set',        # CALL PE,0
    },
    'PF_PARITY_REG': {
        'E0': 'Return if the parity of {} is odd',           # RET PO
        'E20000': 'Jump to #R0 if the parity of {} is odd',  # JP PO,0
        'E40000': 'CALL #R0 if the parity of {} is odd',     # CALL PO,0
        'E8': 'Return if the parity of {} is even',          # RET PE
        'EA0000': 'Jump to #R0 if the parity of {} is even', # JP PE,0
        'EC0000': 'CALL #R0 if the parity of {} is even',    # CALL PE,0
    },
    'PF_OFLOW': {
        'E0': 'Return if there was no overflow',          # RET PO
        'E20000': 'Jump to #R0 if there was no overflow', # JP PO,0
        'E40000': 'CALL #R0 if there was no overflow',    # CALL PO,0
        'E8': 'Return if there was overflow',             # RET PE
        'EA0000': 'Jump to #R0 if there was overflow',    # JP PE,0
        'EC0000': 'CALL #R0 if there was overflow',       # CALL PE,0
    },
    'PF_OFLOW_INC': {
        'E0': 'Return if {}<>#N(128,2,,1)($)',          # RET PO
        'E20000': 'Jump to #R0 if {}<>#N(128,2,,1)($)', # JP PO,0
        'E40000': 'CALL #R0 if {}<>#N(128,2,,1)($)',    # CALL PO,0
        'E8': 'Return if {}=#N(128,2,,1)($)',           # RET PE
        'EA0000': 'Jump to #R0 if {}=#N(128,2,,1)($)',  # JP PE,0
        'EC0000': 'CALL #R0 if {}=#N(128,2,,1)($)',     # CALL PE,0
    },
    'PF_OFLOW_DEC': {
        'E0': 'Return if {}<>#N(127,2,,1)($)',          # RET PO
        'E20000': 'Jump to #R0 if {}<>#N(127,2,,1)($)', # JP PO,0
        'E40000': 'CALL #R0 if {}<>#N(127,2,,1)($)',    # CALL PO,0
        'E8': 'Return if {}=#N(127,2,,1)($)',           # RET PE
        'EA0000': 'Jump to #R0 if {}=#N(127,2,,1)($)',  # JP PE,0
        'EC0000': 'CALL #R0 if {}=#N(127,2,,1)($)',     # CALL PE,0
    },
    'PF_IFF2': {
        'E0': 'Return if interrupts are disabled',          # RET PO
        'E20000': 'Jump to #R0 if interrupts are disabled', # JP PO,0
        'E40000': 'CALL #R0 if interrupts are disabled',    # CALL PO,0
        'E8': 'Return if interrupts are enabled',           # RET PE
        'EA0000': 'Jump to #R0 if interrupts are enabled',  # JP PE,0
        'EC0000': 'CALL #R0 if interrupts are enabled',     # CALL PE,0
    },
    'PF_BLOCK': {
        'E0': 'Return if #REGbc=0',          # RET PO
        'E20000': 'Jump to #R0 if #REGbc=0', # JP PO,0
        'E40000': 'CALL #R0 if #REGbc=0',    # CALL PO,0
        'E8': 'Return if #REGbc>0',          # RET PE
        'EA0000': 'Jump to #R0 if #REGbc>0', # JP PE,0
        'EC0000': 'CALL #R0 if #REGbc>0',    # CALL PE,0
    },
    'PF_BIT': {
        'E0': 'Return if {} is set',            # RET PO
        'E20000': 'Jump to #R0 if {} is set',   # JP PO,0
        'E40000': 'CALL #R0 if {} is set',      # CALL PO,0
        'E8': 'Return if {} is reset',          # RET PE
        'EA0000': 'Jump to #R0 if {} is reset', # JP PE,0
        'EC0000': 'CALL #R0 if {} is reset',    # CALL PE,0
    },
    'CF_NA': {
        '3000': 'Jump to #R32770 if the carry flag is not set', # JR NC,nn
        '3800': 'Jump to #R32770 if the carry flag is set',     # JR C,nn
        'D0': 'Return if the carry flag is not set',            # RET NC
        'D20000': 'Jump to #R0 if the carry flag is not set',   # JP NC,0
        'D40000': 'CALL #R0 if the carry flag is not set',      # CALL NC,0
        'D8': 'Return if the carry flag is set',                # RET C
        'DA0000': 'Jump to #R0 if the carry flag is set',       # JP C,0
        'DC0000': 'CALL #R0 if the carry flag is set',          # CALL C,0
    },
    'CF_COMPARE': {
        '3000': 'Jump to #R32770 if #REGa>={}', # JR NC,nn
        '3800': 'Jump to #R32770 if #REGa<{}',  # JR C,nn
        'D0': 'Return if #REGa>={}',            # RET NC
        'D20000': 'Jump to #R0 if #REGa>={}',   # JP NC,0
        'D40000': 'CALL #R0 if #REGa>={}',      # CALL NC,0
        'D8': 'Return if #REGa<{}',             # RET C
        'DA0000': 'Jump to #R0 if #REGa<{}',    # JP C,0
        'DC0000': 'CALL #R0 if #REGa<{}',       # CALL C,0
    },
    'CF_NEGATE': {
        '3000': 'Jump to #R32770 if #REGa=0', # JR NC,nn
        '3800': 'Jump to #R32770 if #REGa>0', # JR C,nn
        'D0': 'Return if #REGa=0',            # RET NC
        'D20000': 'Jump to #R0 if #REGa=0',   # JP NC,0
        'D40000': 'CALL #R0 if #REGa=0',      # CALL NC,0
        'D8': 'Return if #REGa>0',            # RET C
        'DA0000': 'Jump to #R0 if #REGa>0',   # JP C,0
        'DC0000': 'CALL #R0 if #REGa>0',      # CALL C,0
    },
}

class Instruction:
    def __init__(self, address, data):
        self.address = address
        self.bytes = data

class CommentGeneratorTest(SkoolKitTestCase):
    def test_instructions(self):
        cg = CommentGenerator()
        dummy = Instruction(0x8000, [0])
        for hex_bytes, exp_comment in INSTRUCTIONS.items():
            values = [int(hex_bytes[i:i + 2], 16) for i in range(0, len(hex_bytes), 2)]
            cg.get_comment(dummy) # Clear context
            self.assertEqual(cg.get_comment(Instruction(0x8000, values)), exp_comment, f'Opcodes: {hex_bytes}')

    def test_after_dd(self):
        cg = CommentGenerator()
        for hex_bytes, exp_comment in AFTER_DD.items():
            values = [int(hex_bytes[i:i + 2], 16) for i in range(0, len(hex_bytes), 2)]
            self.assertEqual(cg.get_comment(Instruction(0x8000, values)), exp_comment, f'Opcodes: {hex_bytes}')

    def test_after_fd(self):
        cg = CommentGenerator()
        for hb, c in AFTER_DD.items():
            hex_bytes = 'FD' + hb[2:]
            exp_comment = c.replace('ix', 'iy')
            values = [int(hex_bytes[i:i + 2], 16) for i in range(0, len(hex_bytes), 2)]
            self.assertEqual(cg.get_comment(Instruction(0x8000, values)), exp_comment, f'Opcodes: {hex_bytes}')

    def test_and_n(self):
        cg = CommentGenerator()
        for n in range(256):
            bits = BITS[n]
            if len(bits) == 0:
                exp_comment = '#REGa=0'
            elif len(bits) == 1:
                exp_comment = f'Keep only bit {bits[0]} of #REGa'
            elif len(bits) < 5:
                bits_str = ', '.join(str(b) for b in bits[:-1]) + f' and {bits[-1]}'
                exp_comment = f'Keep only bits {bits_str} of #REGa'
            else:
                nbits = [b for b in range(8) if b not in bits]
                if len(nbits) == 0:
                    exp_comment = 'Set the zero flag if #REGa=0, and reset the carry flag'
                elif len(nbits) == 1:
                    exp_comment = f'Reset bit {nbits[0]} of #REGa'
                else:
                    nbits_str = ', '.join(str(b) for b in nbits[:-1]) + f' and {nbits[-1]}'
                    exp_comment = f'Reset bits {nbits_str} of #REGa'
            self.assertEqual(cg.get_comment(Instruction(0x8000, (0xE6, n))), exp_comment)

    def test_or_n(self):
        cg = CommentGenerator()
        for n in range(256):
            bits = BITS[n]
            if len(bits) == 0:
                exp_comment = 'Set the zero flag if #REGa=0, and reset the carry flag'
            elif len(bits) == 1:
                exp_comment = f'Set bit {bits[0]} of #REGa'
            elif len(bits) < 8:
                bits_str = ', '.join(str(b) for b in bits[:-1]) + f' and {bits[-1]}'
                exp_comment = f'Set bits {bits_str} of #REGa'
            else:
                exp_comment = '#REGa=#N(255,2,,1)($)'
            self.assertEqual(cg.get_comment(Instruction(0x8000, (0xF6, n))), exp_comment)

    def test_xor_n(self):
        cg = CommentGenerator()
        for n in range(256):
            bits = BITS[n]
            if len(bits) == 0:
                exp_comment = 'Set the zero flag if #REGa=0, and reset the carry flag'
            elif len(bits) == 1:
                exp_comment = f'Flip bit {bits[0]} of #REGa'
            elif len(bits) < 8:
                bits_str = ', '.join(str(b) for b in bits[:-1]) + f' and {bits[-1]}'
                exp_comment = f'Flip bits {bits_str} of #REGa'
            else:
                exp_comment = 'Flip every bit of #REGa'
            self.assertEqual(cg.get_comment(Instruction(0x8000, (0xEE, n))), exp_comment)

    def test_cp_n(self):
        cg = CommentGenerator()
        for n in range(256):
            if n:
                exp_comment = f'Set the zero flag if #REGa=#N({n},2,,1)($), or the carry flag if #REGa<#N({n},2,,1)($)'
            else:
                exp_comment = 'Set the zero flag if #REGa=0, and reset the carry flag'
            self.assertEqual(cg.get_comment(Instruction(0x8000, (0xFE, n))), exp_comment)

    def test_jr_address(self):
        cg = CommentGenerator()
        for opcode, cond in (
                (0x18, ''),
                (0x20, ' if the zero flag is not set'),
                (0x28, ' if the zero flag is set'),
                (0x30, ' if the carry flag is not set'),
                (0x38, ' if the carry flag is set')
            ):
            for addr in (0x0000, 0x8000, 0xFFFE, 0xFFFF):
                for offset in (0x40, 0xA0):
                    jr_addr = (addr + 2 + offset - 256 * (offset > 0x7F)) % 65536
                    comment = cg.get_comment(Instruction(addr, (opcode, offset)))
                    self.assertEqual(comment, f'Jump to #R{jr_addr}{cond}', f'Opcodes: {opcode:02X}{offset:02X}')

class ConditionalCallJumpRetTest(SkoolKitTestCase):
    def _inc_dec_opcodes(self, base):
        opcodes = []
        for i, r in enumerate(('#REGb', '#REGc', '#REGd', '#REGe', '#REGh', '#REGl', '(PEEK #REGhl)', '#REGa')):
            opcodes.append((f'{base + 8 * i:02X}', r))
        for prefix, r in (('DD', '#REGix'), ('FD', '#REGiy')):
            for suffix, reg in ((f'{base + 0x20:02X}', f'{r}h'), (f'{base + 0x28:02X}', f'{r}l'), (f'{base + 0x30:02X}00', f'(PEEK ({r}+#N(0,2,,1)($)))')):
                opcodes.append((prefix + suffix, reg))
        return opcodes

    def _alo_opcodes(self, base):
        opcodes = [f'{b:02X}' for b in range(base, base + 8)] # ALO A,r
        opcodes.append(f'{base + 0x46:02X}00') # ALO A,0
        for prefix in ('DD', 'FD'):
            for suffix in (f'{base + 4:02X}', f'{base + 5:02X}', f'{base + 6:02X}00'):
                opcodes.append(prefix + suffix) # ALO A,XYh/XYl/(XY+0)
        return opcodes

    def _sro_opcodes(self, base):
        opcodes = []
        for i, r in enumerate(('#REGb', '#REGc', '#REGd', '#REGe', '#REGh', '#REGl', '(PEEK #REGhl)', '#REGa')):
            opcodes.append((f'CB{base + i:02X}', r))
        for prefix, xy in (('DD', '#REGix'), ('FD', '#REGiy')):
            for i, r in enumerate(('#REGb', '#REGc', '#REGd', '#REGe', '#REGh', '#REGl', f'(PEEK ({xy}+#N(0,2,,1)($)))', '#REGa')):
                opcodes.append((f'{prefix}CB00{base + i:02X}', r))
        return opcodes

    def _test_conditionals(self, cg, op_hex, reg, *conditionals):
        addr = 0x8000
        op_v = [int(op_hex[i:i + 2], 16) for i in range(0, len(op_hex), 2)]

        # Conditional CALL/JP/JR/RET immediately after test instruction
        instruction = Instruction(addr - len(op_v), op_v)
        for name in conditionals:
            for cond, exp_comment in CONDITIONALS[name].items():
                cg.get_comment(instruction)
                cond_v = [int(cond[i:i + 2], 16) for i in range(0, len(cond), 2)]
                self.assertEqual(cg.get_comment(Instruction(addr, cond_v)), exp_comment.format(reg), f'Opcodes: {op_hex} {cond}')

        # NOP between test instruction and conditional CALL/JP/JR/RET clears context
        nop = Instruction(addr - 1, [0])
        instruction.address = nop.address - len(op_v)
        for name in ('SF_NA', 'ZF_NA', 'PF_NA', 'CF_NA'):
            for cond, exp_comment in CONDITIONALS[name].items():
                cg.get_comment(instruction)
                cg.get_comment(nop)
                cond_v = [int(cond[i:i + 2], 16) for i in range(0, len(cond), 2)]
                self.assertEqual(cg.get_comment(Instruction(addr, cond_v)), exp_comment.format(reg), f'Opcodes: {op_hex} 00 {cond}')

    def test_inc(self):
        cg = CommentGenerator()
        for op_hex, reg in self._inc_dec_opcodes(0x04):
            self._test_conditionals(cg, op_hex, reg, 'SF_SIGN', 'ZF_ZERO', 'PF_OFLOW_INC', 'CF_NA')

    def test_dec(self):
        cg = CommentGenerator()
        for op_hex, reg in self._inc_dec_opcodes(0x05):
            self._test_conditionals(cg, op_hex, reg, 'SF_SIGN', 'ZF_ZERO', 'PF_OFLOW_DEC', 'CF_NA')

    def test_add_a(self):
        cg = CommentGenerator()
        for op_hex in self._alo_opcodes(0x80):
            self._test_conditionals(cg, op_hex, '#REGa', 'SF_SIGN', 'ZF_ZERO', 'PF_OFLOW', 'CF_NA')

    def test_adc_a(self):
        cg = CommentGenerator()
        for op_hex in self._alo_opcodes(0x88):
            self._test_conditionals(cg, op_hex, '#REGa', 'SF_SIGN', 'ZF_ZERO', 'PF_OFLOW', 'CF_NA')

    def test_sub(self):
        cg = CommentGenerator()
        for op_hex in self._alo_opcodes(0x90):
            self._test_conditionals(cg, op_hex, '#REGa', 'SF_SIGN', 'ZF_ZERO', 'PF_OFLOW', 'CF_NA')

    def test_sbc_a(self):
        cg = CommentGenerator()
        for op_hex in self._alo_opcodes(0x98):
            self._test_conditionals(cg, op_hex, '#REGa', 'SF_SIGN', 'ZF_ZERO', 'PF_OFLOW', 'CF_NA')

    def test_and(self):
        cg = CommentGenerator()
        for op_hex in self._alo_opcodes(0xA0):
            self._test_conditionals(cg, op_hex, '#REGa', 'SF_SIGN', 'ZF_ZERO', 'PF_PARITY_REG', 'CF_NA')

    def test_xor(self):
        cg = CommentGenerator()
        for op_hex in self._alo_opcodes(0xA8):
            self._test_conditionals(cg, op_hex, '#REGa', 'SF_SIGN', 'ZF_ZERO', 'PF_PARITY_REG', 'CF_NA')

    def test_or(self):
        cg = CommentGenerator()
        for op_hex in self._alo_opcodes(0xB0):
            self._test_conditionals(cg, op_hex, '#REGa', 'SF_SIGN', 'ZF_ZERO', 'PF_PARITY_REG', 'CF_NA')

    def test_cp_r(self):
        cg = CommentGenerator()
        for op_hex, reg in (
                ('B8', '#REGb'),
                ('B9', '#REGc'),
                ('BA', '#REGd'),
                ('BB', '#REGe'),
                ('BC', '#REGh'),
                ('BD', '#REGl'),
                ('BE', 'PEEK #REGhl'),
                ('DDBC', '#REGixh'),
                ('DDBD', '#REGixl'),
                ('DDBE00', 'PEEK (#REGix+#N(0,2,,1)($))'),
                ('FDBC', '#REGiyh'),
                ('FDBD', '#REGiyl'),
                ('FDBE00', 'PEEK (#REGiy+#N(0,2,,1)($))'),
        ):
            self._test_conditionals(cg, op_hex, reg, 'SF_NA', 'ZF_COMPARE', 'PF_OFLOW', 'CF_COMPARE')

    def test_cp_n(self):
        cg = CommentGenerator()
        for n in range(256):
            self._test_conditionals(cg, f'FE{n:02X}', f'#N({n},2,,1)($)', 'SF_NA', 'ZF_COMPARE', 'PF_OFLOW', 'CF_COMPARE' if n else 'CF_NA')

    def test_rlc(self):
        cg = CommentGenerator()
        for op_hex, reg in self._sro_opcodes(0x00):
            self._test_conditionals(cg, op_hex, reg, 'SF_SIGN', 'ZF_ZERO', 'PF_PARITY_REG', 'CF_NA')

    def test_rrc(self):
        cg = CommentGenerator()
        for op_hex, reg in self._sro_opcodes(0x08):
            self._test_conditionals(cg, op_hex, reg, 'SF_SIGN', 'ZF_ZERO', 'PF_PARITY_REG', 'CF_NA')

    def test_rl(self):
        cg = CommentGenerator()
        for op_hex, reg in self._sro_opcodes(0x10):
            self._test_conditionals(cg, op_hex, reg, 'SF_SIGN', 'ZF_ZERO', 'PF_PARITY_REG', 'CF_NA')

    def test_rr(self):
        cg = CommentGenerator()
        for op_hex, reg in self._sro_opcodes(0x18):
            self._test_conditionals(cg, op_hex, reg, 'SF_SIGN', 'ZF_ZERO', 'PF_PARITY_REG', 'CF_NA')

    def test_sla(self):
        cg = CommentGenerator()
        for op_hex, reg in self._sro_opcodes(0x20):
            self._test_conditionals(cg, op_hex, reg, 'SF_SIGN', 'ZF_ZERO', 'PF_PARITY_REG', 'CF_NA')

    def test_sra(self):
        cg = CommentGenerator()
        for op_hex, reg in self._sro_opcodes(0x28):
            self._test_conditionals(cg, op_hex, reg, 'SF_SIGN', 'ZF_ZERO', 'PF_PARITY_REG', 'CF_NA')

    def test_sll(self):
        cg = CommentGenerator()
        for op_hex, reg in self._sro_opcodes(0x30):
            self._test_conditionals(cg, op_hex, reg, 'SF_SIGN', 'ZF_ZERO', 'PF_PARITY_REG', 'CF_NA')

    def test_srl(self):
        cg = CommentGenerator()
        for op_hex, reg in self._sro_opcodes(0x38):
            self._test_conditionals(cg, op_hex, reg, 'SF_SIGN', 'ZF_ZERO', 'PF_PARITY_REG', 'CF_NA')

    def test_rrd_rld(self):
        cg = CommentGenerator()
        for op_hex in ('ED67', 'ED6F'):
            self._test_conditionals(cg, op_hex, '#REGa', 'SF_SIGN', 'ZF_ZERO', 'PF_PARITY_REG', 'CF_NA')

    def test_in_c(self):
        cg = CommentGenerator()
        for i, r in enumerate(('b', 'c', 'd', 'e', 'h', 'l', '', 'a')):
            if r:
                op_hex = f'ED{0x40 + i * 8:02X}'
                self._test_conditionals(cg, op_hex, f'#REG{r}', 'SF_SIGN', 'ZF_ZERO', 'PF_PARITY_REG', 'CF_NA')

    def test_daa(self):
        cg = CommentGenerator()
        self._test_conditionals(cg, '27', '#REGa', 'SF_SIGN', 'ZF_ZERO', 'PF_PARITY_REG', 'CF_NA')

    def test_neg(self):
        cg = CommentGenerator()
        for opcode in range(0x44, 0x84, 8):
            self._test_conditionals(cg, f'ED{opcode:02X}', '#REGa', 'SF_SIGN', 'ZF_ZERO', 'PF_PARITY_REG', 'CF_NEGATE')

    def test_sbc_hl(self):
        cg = CommentGenerator()
        for opcode in range(0x42, 0x82, 0x10):
            self._test_conditionals(cg, f'ED{opcode:02X}', '#REGhl', 'SF_SIGN', 'ZF_ZERO', 'PF_OFLOW', 'CF_NA')

    def test_adc_hl(self):
        cg = CommentGenerator()
        for opcode in range(0x4A, 0x8A, 0x10):
            self._test_conditionals(cg, f'ED{opcode:02X}', '#REGhl', 'SF_SIGN', 'ZF_ZERO', 'PF_OFLOW', 'CF_NA')

    def test_ini_outi_ind_outd(self):
        cg = CommentGenerator()
        for op_hex in ('EDA2', 'EDA3', 'EDAA', 'EDAB'):
            self._test_conditionals(cg, op_hex, '#REGb', 'SF_SIGN', 'ZF_ZERO', 'PF_PARITY', 'CF_NA')

    def test_cpi_cpd_cpir_cpdr(self):
        cg = CommentGenerator()
        for op_hex in ('EDA1', 'EDA9', 'EDB1', 'EDB9'):
            self._test_conditionals(cg, op_hex, 'PEEK #REGhl', 'SF_NA', 'ZF_COMPARE', 'PF_BLOCK', 'CF_NA')

    def test_ldi_ldd(self):
        cg = CommentGenerator()
        for op_hex in ('EDA0', 'EDA8'):
            self._test_conditionals(cg, op_hex, '', 'SF_NA', 'ZF_NA', 'PF_BLOCK', 'CF_NA')

    def test_ld_a_i_r(self):
        cg = CommentGenerator()
        for op_hex in ('ED57', 'ED5F'):
            self._test_conditionals(cg, op_hex, '#REGa', 'SF_SIGN', 'ZF_ZERO', 'PF_IFF2', 'CF_NA')

    def test_bit_b_r(self):
        cg = CommentGenerator()
        for b in range(8):
            sf_group = 'SF_BIT_7' if b == 7 else 'SF_NA'
            for i, r in enumerate(('#REGb', '#REGc', '#REGd', '#REGe', '#REGh', '#REGl', 'PEEK #REGhl', '#REGa')):
                op_hex = f'CB{0x40 + 8 * b + i:02X}'
                ctx = f'bit {b} of {r}'
                self._test_conditionals(cg, op_hex, ctx, sf_group, 'ZF_BIT', 'PF_BIT', 'CF_NA')

    def test_bit_b_xy(self):
        cg = CommentGenerator()
        for b in range(8):
            sf_group = 'SF_BIT_7' if b == 7 else 'SF_NA'
            for prefix, r in (('DD', '#REGix'), ('FD', '#REGiy')):
                ctx = f'bit {b} of PEEK ({r}+#N(0,2,,1)($))'
                for i in range(8):
                    op_hex = f'{prefix}CB00{0x40 + 8 * b + i:02X}'
                    self._test_conditionals(cg, op_hex, ctx, sf_group, 'ZF_BIT', 'PF_BIT', 'CF_NA')

    def test_rlca_rrca_rla_rra(self):
        cg = CommentGenerator()
        for op_hex in ('07', '0F', '17', '1F'):
            self._test_conditionals(cg, op_hex, '', 'SF_NA', 'ZF_NA', 'PF_NA', 'CF_NA')

    def test_add_hl_xy(self):
        cg = CommentGenerator()
        for prefix in ('', 'DD', 'FD'):
            for opcode in range(0x09, 0x49, 0x10):
                op_hex = f'{prefix}{opcode:02X}'
                self._test_conditionals(cg, op_hex, '', 'SF_NA', 'ZF_NA', 'PF_NA', 'CF_NA')
