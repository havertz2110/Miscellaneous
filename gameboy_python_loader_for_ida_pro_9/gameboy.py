import idaapi
import idc
import ida_bytes
import ida_funcs

# aliases so you can keep using the old names
MakeName     = lambda ea, name: idc.set_name(ea, name, idc.SN_NOWARN)
MakeData     = lambda ea, fmt, sz, tid: ida_bytes.create_data(ea, fmt, sz, tid)
MakeFunction = lambda ea: ida_funcs.add_func(ea)
create_strlit= lambda start, end: idc.create_strlit(start, end)

# Nintendo logo bytes at header offset 0x104
logo = bytes.fromhex(
    "CEED6666CC0D000B03730083000C000D0008111F8889000EDCCC6EE6DDDDD"
    "999BBBB67636E0EECCCDDDC999FBBB9333E"
)

registers = {
    0xFF00: "rJOYP", 0xFF01: "rSB",    0xFF02: "rSC",    0xFF04: "rDIV",
    0xFF05: "rTIMA", 0xFF06: "rTMA",   0xFF07: "rTAC",   0xFF0F: "rIF",
    0xFF10: "rNR10", 0xFF11: "rNR11",  0xFF12: "rNR12",  0xFF13: "rNR13",
    0xFF14: "rNR14", 0xFF16: "rNR21",  0xFF17: "rNR22",  0xFF18: "rNR23",
    0xFF19: "rNR24", 0xFF1A: "rNR30",  0xFF1B: "rNR31",  0xFF1C: "rNR32",
    0xFF1D: "rNR33", 0xFF1E: "rNR34",  0xFF20: "rNR41",  0xFF21: "rNR42",
    0xFF22: "rNR43", 0xFF23: "rNR44",  0xFF24: "rNR50",  0xFF25: "rNR51",
    0xFF26: "rNR52", 0xFF30: "rWAV",   0xFF40: "rLCDC",  0xFF41: "rSTAT",
    0xFF42: "rSCY",  0xFF43: "rSCX",   0xFF44: "rLY",    0xFF45: "rLYC",
    0xFF46: "rDMA",  0xFF47: "rBGP",   0xFF48: "rOBP0",  0xFF49: "rOBP1",
    0xFF4A: "rWY",   0xFF4B: "rWX",    0xFF4D: "rKEY1",  0xFF4F: "rVBK",
    0xFF51: "rHDMA1",0xFF52: "rHDMA2", 0xFF53: "rHDMA3", 0xFF54: "rHDMA4",
    0xFF55: "rHDMA5",0xFF56: "rRP",    0xFF68: "rBGPI",  0xFF69: "rBGPD",
    0xFF6A: "rOBPI", 0xFF6B: "rOBPD",  0xFF70: "rSVBK",  0xFF76: "rPCM12",
    0xFF77: "rPCM34",0xFFFF: "rIE",
}

def accept_file(li, filename):
    li.seek(0x104)
    if li.read(0x30) != logo:
        return 0
    return {'format': "Game Boy ROM", 'processor': 'gb'}

def add_seg(start, end, bank, name):
    seg = idaapi.segment_t()
    seg.start_ea = start + bank*0x10000
    seg.end_ea   = end   + bank*0x10000
    seg.sel      = idaapi.setup_selector(bank*0x1000)
    seg.bitness  = 0
    seg.align    = idaapi.saRelPara
    seg.comb     = idaapi.scPub
    idaapi.add_segm_ex(seg, name, "", idaapi.ADDSEG_NOSREG|idaapi.ADDSEG_OR_DIE)

def load_file(li, neflags, format):
    size = (li.size() + 0x3FFF) & ~0x3FFF
    idaapi.set_processor_type("gb", idaapi.SETPROC_LOADER)

    # ROM0
    add_seg(0x0000, 0x4000, 0, "ROM0")
    li.file2base(0, 0, 0x4000, True)

    # switchable banks
    for b in range(1, size//0x4000):
        add_seg(0x4000, 0x8000, b, f"ROM{b:02X}")
        li.file2base(0x4000*b, 0x4000 + b*0x10000, 0x8000 + b*0x10000, True)

    # SRAM size from header byte 0x149
    li.seek(0x149)
    code = li.read(1)[0]
    sram_banks = [0,1,1,4,16,8][code] if code < 6 else 0

    add_seg(0x8000, 0xA000, 0, "VRAM")
    for i in range(sram_banks):
        add_seg(0xA000, 0xC000, i, f"SRAM{i:X}")

    # CGB check
    li.seek(0x143)
    is_cgb = bool(li.read(1)[0] & 0x80)
    if is_cgb:
        add_seg(0xC000, 0xD000, 0, "WRAM0")
        for b in range(1,8):
            add_seg(0xD000, 0xE000, b, f"WRAM{b}")
    else:
        add_seg(0xC000, 0xE000, 0, "WRAM")

    # OAM, MMIO, HRAM, IE
    add_seg(0xFE00, 0xFEA0, 0, "OAM")
    add_seg(0xFF00, 0xFF80, 0, "MMIO")
    add_seg(0xFF80, 0xFFFF, 0, "HRAM")
    add_seg(0xFFFF, 0x10000, 0, "IE")

    # name & data regs
    for ea,nm in registers.items():
        MakeName(ea,nm)
        MakeData(ea, 0, 16 if nm=="rWAV" else 1, 0)

    # entrypoint & interrupt vectors
    MakeFunction(0x100)
    MakeName(0x100, "Start")
    irq_names = [
      "Rst00","Rst08","Rst10","Rst18","Rst20","Rst28","Rst30","Rst38",
      "VBlankInterrupt","StatInterrupt","TimerInterrupt",
      "SerialInterrupt","JoypadInterrupt"
    ]
    for i in range(12,-1,-1):
        ea = i*8
        li.seek(ea)
        if li.read(1)[0] not in (0x00,0xFF):
            MakeFunction(ea)
            MakeName(ea, irq_names[i])

    # header structures
    MakeData(0x104, 0, 0x30, 0); MakeName(0x104, "NintendoLogo")
    if is_cgb:
        create_strlit(0x134, 0x143)
        MakeName(0x134, "Title")
        MakeData(0x143,0,1,0); MakeName(0x143,"CgbFlag")
    else:
        create_strlit(0x134, 0x144)
        MakeName(0x134, "Title")

    # licensee code
    li.seek(0x14B)
    newlic = (li.read(1)==b'\x33')
    create_strlit(0x144, 0x146)
    MakeName(0x144, "LicenseeCode" if newlic else "OldLicenseeCode")

    # other header bytes
    MakeData(0x146,0,1,0); MakeName(0x146,"SgbFlag")
    MakeData(0x147,0,1,0); MakeName(0x147,"CartridgeType")
    MakeData(0x148,0,1,0); MakeName(0x148,"RomSize")
    MakeData(0x149,0,1,0); MakeName(0x149,"RamSize")
    MakeData(0x14A,0,1,0); MakeName(0x14A,"DestinationCode")
    MakeData(0x14B,0,1,0)
    MakeData(0x14C,0,1,0); MakeName(0x14C,"Version")
    MakeData(0x14D,0,1,0); MakeName(0x14D,"HeaderChecksum")
    MakeData(0x14E,0,2,0); MakeName(0x14E,"GlobalChecksum")

    return 1