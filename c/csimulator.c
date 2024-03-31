/*
  Copyright 2024 Richard Dymond (rjdymond@gmail.com)

  This file is part of SkoolKit.

  SkoolKit is free software: you can redistribute it and/or modify it under the
  terms of the GNU General Public License as published by the Free Software
  Foundation, either version 3 of the License, or (at your option) any later
  version.

  SkoolKit is distributed in the hope that it will be useful, but WITHOUT ANY
  WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
  A PARTICULAR PURPOSE. See the GNU General Public License for more details.

  You should have received a copy of the GNU General Public License along with
  SkoolKit. If not, see <http://www.gnu.org/licenses/>.
*/

#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include "structmember.h"

#define REG(r) reg[r]
#define MEMGET(a) (mem ? mem[a] : self->mem128[(a) / 0x4000][(a) % 0x4000])
#define MEMSET(a, v) if (mem) mem[a] = v; else self->mem128[(a) / 0x4000][(a) % 0x4000] = v
#define INC_R(i) REG(R) = (REG(R) & 0x80) + ((REG(R) + (i)) & 0x7F)
#ifdef CONTENTION
#define CONTEND unsigned t = REG(T) % self->frame_duration; unsigned delay = 0; if (self->t0 < t && t < self->t1)
#define CPATTERN(...) self->contend(&t, &delay, self->out7ffd & 1, __VA_ARGS__)
#define INC_T(i) REG(T) += i + delay
#else
#define INC_T(i) REG(T) += i
#endif
#define INC_PC(i) REG(PC) = (REG(PC) + (i)) % 65536
#define OUT(p, v) if (mem == NULL && (p & 0x8002) == 0 && (self->out7ffd & 0x20) == 0) out7ffd(self, v)

typedef unsigned char byte;

typedef void (*contend_f)(unsigned* t, unsigned* delay, int urc, int n, ...);

typedef struct CSimulatorObject CSimulatorObject;

typedef void (*opcode_exec)(CSimulatorObject* self, void* lookup, int args[]);

typedef struct {
    opcode_exec func;
    void* lookup;
    int args[7];
} OpcodeFunction;

typedef struct CSimulatorObject {
    PyObject_HEAD
    Py_buffer buffers[11];
    unsigned long long* registers;
    byte* memory;
    byte* roms[2];
    byte* banks[8];
    byte* mem128[4];
    unsigned frame_duration;
    unsigned int_active;
#ifdef CONTENTION
    unsigned t0;
    unsigned t1;
    contend_f contend;
#endif
    byte out7ffd;
    PyObject* memory_obj;
    PyObject* registers_obj;
    PyObject* tracer;
    PyObject* in_a_n_tracer;
    PyObject* in_r_c_tracer;
    PyObject* ini_tracer;
    PyObject* out_tracer;
    OpcodeFunction* opcodes[256];
} CSimulatorObject;

typedef struct {
    PyObject* name;
    byte opcode;
    unsigned* code;
    int c0;
    int c1;
    unsigned in_time;
    unsigned loop_time;
    unsigned loop_r_inc;
    unsigned ear_mask;
    unsigned polarity;
    unsigned* state;
    unsigned hits;
} tsl_accelerator;

static const int A = 0;
static const int F = 1;
static const int B = 2;
static const int C = 3;
static const int D = 4;
static const int E = 5;
static const int H = 6;
static const int L = 7;
static const int SP = 12;
static const int I = 14;
static const int R = 15;
static const int xA = 16;
static const int xF = 17;
static const int xB = 18;
static const int xC = 19;
static const int xD = 20;
static const int xE = 21;
static const int xH = 22;
static const int xL = 23;
static const int PC = 24;
static const int T = 25;
static const int IFF = 26;
static const int IM = 27;
static const int HALT = 28;

typedef struct {
    const char* name;
    unsigned index;
    unsigned size;
    unsigned mask;
} z80_reg;

z80_reg REGISTERS[] = {
    {"A", 0, 1, 0xFF},
    {"F", 1, 1, 0xFF},
    {"B", 2, 1, 0xFF},
    {"C", 3, 1, 0xFF},
    {"D", 4, 1, 0xFF},
    {"E", 5, 1, 0xFF},
    {"H", 6, 1, 0xFF},
    {"L", 7, 1, 0xFF},
    {"IXh", 8, 1, 0xFF},
    {"IXl", 9, 1, 0xFF},
    {"IYh", 10, 1, 0xFF},
    {"IYl", 11, 1, 0xFF},
    {"SP", 12, 1, 0xFFFF},
    {"I", 14, 1, 0xFF},
    {"R", 15, 1, 0xFF},
    {"^A", 16, 1, 0xFF},
    {"^F", 17, 1, 0xFF},
    {"^B", 18, 1, 0xFF},
    {"^C", 19, 1, 0xFF},
    {"^D", 20, 1, 0xFF},
    {"^E", 21, 1, 0xFF},
    {"^H", 22, 1, 0xFF},
    {"^L", 23, 1, 0xFF},
    {"PC", 24, 1, 0xFFFF},
    {"T", 25, 1, 0xFFFFFFFF},
    {"BC", 2, 2, 0xFF},
    {"DE", 4, 2, 0xFF},
    {"HL", 6, 2, 0xFF},
    {"IX", 8, 2, 0xFF},
    {"IY", 10, 2, 0xFF},
    {"^BC", 18, 2, 0xFF},
    {"^DE", 20, 2, 0xFF},
    {"^HL", 22, 2, 0xFF},
    {NULL}
};

z80_reg STATE[] = {
    {"iff", 26},
    {"im", 27},
    {"halted", 28},
    {"tstates", 25},
    {NULL}
};

static byte PARITY[256];
static byte SZ53P[256];
static byte ADC[2][256][256][2];
static byte ADC_A_A[2][256][2];
static byte ADD[256][256][2];
static byte AND[256][256][2];
static byte BIT[2][8][256];
static byte CCF[256][256];
static byte CP[256][256][2];
static byte CPL[256][256][2];
static byte DAA[256][256][2];
static byte DEC[2][256][2];
static byte INC[2][256][2];
static byte NEG[256][2];
static byte OR[256][256][2];
static byte RL[2][256][2];
static byte RLC[256][2];
static byte RR[2][256][2];
static byte RRC[256][2];
static byte RLA[256][256][2];
static byte RLCA[256][256][2];
static byte RRA[256][256][2];
static byte RRCA[256][256][2];
static byte SBC[2][256][256][2];
static byte SBC_A_A[2][256][2];
static byte SCF[256][256];
static byte SLA[256][2];
static byte SLL[256][2];
static byte SRA[256][2];
static byte SRL[256][2];
static byte SUB[256][256][2];
static byte XOR[256][256][2];

#ifdef CONTENTION
static byte DELAYS_48K[69888];
static byte DELAYS_128K[70908];
#endif

static void init_PARITY() {
    if (PARITY[0] == 0) {
        for (int i = 0; i < 256; i++) {
            int count = 0;
            int v = i;
            while (v) {
                count += v & 1;
                v = v / 2;
            }
            PARITY[i] = (count & 1) ? 0 : 4;
        }
    }
}

static void init_SZ53P() {
    init_PARITY();
    if (SZ53P[0] == 0) {
        for (int i = 0; i < 256; i++) {
            SZ53P[i] = (
                (i & 0xA8)            // S.5.3...
                + (i == 0 ? 0x40 : 0) // .Z......
                + PARITY[i]           // .....P..
            );
        }
    }
}

static void init_ADC() {
    if (ADC[1][0][0][0] == 0) {
        for (int c = 0; c < 2; c++) {
            for (int a = 0; a < 256; a++) {
                for (int i = 0; i < 256; i++) {
                    int v = i + a + c;
                    ADC[c][a][i][0] = v & 0xFF;
                    ADC[c][a][i][1] = (
                        (v & 0xA8)                                           // S.5.3.N.
                        + (((v & 0xFF) == 0) ? 0x40 : 0)                     // .Z......
                        + (((a & 0x0F) + ((v - a) & 0x0F)) & 0x10)           // ...H....
                        + (((a ^ (v - c - a) ^ 0x80) & (a ^ v) & 0x80) >> 5) // .....P..
                        + ((v > 0xFF) ? 0x01 : 0)                            // .......C
                    );
                }
            }
        }
    }
}

static void init_ADC_A_A() {
    init_ADC();
    if (ADC_A_A[1][0][0] == 0) {
        for (int c = 0; c < 2; c++) {
            for (int a = 0; a < 256; a++) {
                ADC_A_A[c][a][0] = ADC[c][a][a][0];
                ADC_A_A[c][a][1] = ADC[c][a][a][1] | (((a & 0x0F) == 0x0F) ? 0x10 : 0);
            }
        }
    }
}

static void init_ADD() {
    init_ADC();
    if (ADD[1][0][0] == 0) {
        for (int a = 0; a < 256; a++) {
            for (int n = 0; n < 256; n++) {
                ADD[a][n][0] = ADC[0][a][n][0];
                ADD[a][n][1] = ADC[0][a][n][1];
            }
        }
    }
}

static void init_AND() {
    init_SZ53P();
    if (AND[1][1][0] == 0) {
        for (int a = 0; a < 256; a++) {
            for (int n = 0; n < 256; n++) {
                AND[a][n][0] = a & n;
                AND[a][n][1] = SZ53P[a & n] + 0x10;
            }
        }
    }
}

static void init_BIT() {
    if (BIT[0][0][0] == 0) {
        for (int c = 0; c < 2; c++) {
            for (int b = 0; b < 8; b++) {
                for (int r = 0; r < 256; r++) {
                    BIT[c][b][r] = (
                        ((b == 7 && r & 0x80) ? 0x80 : 0)    // S.....N.
                        + (((r & (1 << b)) == 0) ? 0x44 : 0) // .Z...P..
                        + (r & 0x28)                         // ..5.3...
                        + 0x10                               // ...H....
                        + c                                  // .......C
                    );
                }
            }
        }
    }
}

static void init_CCF() {
    if (CCF[0][0] == 0) {
        for (int f = 0; f < 256; f++) {
            for (int a = 0; a < 256; a++) {
                CCF[f][a] = (
                    (f & 0xC4)             // SZ...PN.
                    + (a & 0x28)           // ..5.3...
                    + (f & 0x01) * 15 + 1  // ...H...C
                );
            }
        }
    }
}

static void init_CP() {
    if (CP[0][0][0] == 0) {
        for (int a = 0; a < 256; a++) {
            for (int n = 0; n < 256; n++) {
                CP[a][n][0] = a;
                CP[a][n][1] = (
                    ((a - n) & 0x80)                          // S.......
                    + (a == n ? 0x40 : 0)                     // .Z......
                    + (n & 0x28)                              // ..5.3...
                    + (((a & 0x0F) - (n & 0x0F)) & 0x10)      // ...H....
                    + (((a ^ n) & (a ^ (a - n)) & 0x80) >> 5) // .....P..
                    + 0x02                                    // ......N.
                    + (n > a ? 1 : 0)                         // .......C
                );
            }
        }
    }
}

static void init_CPL() {
    if (CPL[0][0][0] == 0) {
        for (int a = 0; a < 256; a++) {
            for (int f = 0; f < 256; f++) {
                CPL[a][f][0] = a ^ 255;
                CPL[a][f][1] = (
                    (f & 0xC5)           // SZ...P.C
                    + ((a ^ 255) & 0x28) // ..5.3...
                    + 0x12               // ...H..N.
                );
            }
        }
    }
}

static void init_DAA() {
    init_SZ53P();
    if (DAA[255][0][0] == 0) {
        for (int a = 0; a < 256; a++) {
            for (int f = 0; f < 256; f++) {
                byte d = (f & 0x10) / 4 + (f & 0x03);
                byte daa = (a + ((d > 3 || (a & 0x0F) > 9) * 6 + (d & 1 || a > 0x99) * 0x60) * (1 - (d & 2))) & 0xFF;
                DAA[a][f][0] = daa;
                DAA[a][f][1] = (
                    SZ53P[daa]                                                               // SZ5.3P..
                    + ((d > 5 && (a & 0x0F) < 6) || ((d & 2) == 0 && (a & 0x0F) > 9)) * 0x10 // ...H....
                    + (d & 0x02)                                                             // ......N.
                    + (d & 1 || a > 0x99)                                                    // .......C
                );
            }
        }
    }
}

static void init_DEC() {
    if (DEC[0][0][0] == 0) {
        for (int c = 0; c < 2; c++) {
            for (int v = -1; v < 255; v++) {
                DEC[c][v + 1][0] = v % 256;
                DEC[c][v + 1][1] = (
                    (v & 0xA8)                          // S.5.3...
                    + ((v == 0) ? 0x40 : 0)             // .Z......
                    + (((v & 0x0F) == 0x0F) ? 0x10 : 0) // ...H....
                    + ((v == 0x7F) ? 0x04 : 0)          // .....P..
                    + 0x02                              // ......N.
                    + c                                 // .......C
                );
            }
        }
    }
}

static void init_INC() {
    if (INC[0][0][0] == 0) {
        for (int c = 0; c < 2; c++) {
            for (int v = 1; v < 257; v++) {
                INC[c][v - 1][0] = v % 256;
                INC[c][v - 1][1] = (
                    (v & 0xA8)                       // S.5.3...
                    + ((v == 256) ? 0x40 : 0)        // .Z......
                    + (((v & 0x0F) == 0) ? 0x10 : 0) // ...H....
                    + ((v == 0x80) ? 0x04 : 0)       // .....P..
                    + c                              // .......C
                );
            }
        }
    }
}

static void init_NEG() {
    if (NEG[1][0] == 0) {
        for (int i = 0; i < 256; i++) {
            int v = 256 - i;
            NEG[i][0] = v & 0xFF;
            NEG[i][1] = (
                (v & 0xA8)               // S.5.3...
                + (v == 256 ? 0x40 : 0)  // .Z......
                + (v & 0x0F ? 0x10 : 0)  // ...H....
                + (v == 0x80 ? 0x04 : 0) // .....P..
                + 0x02                   // ......N.
                + (v < 256 ? 0x01 : 0)   // .......C
            );
        }
    }
}

static void init_OR() {
    init_SZ53P();
    if (OR[1][0][0] == 0) {
        for (int a = 0; a < 256; a++) {
            for (int n = 0; n < 256; n++) {
                OR[a][n][0] = a | n;
                OR[a][n][1] = SZ53P[a | n];
            }
        }
    }
}

static void init_RL() {
    init_SZ53P();
    if (RL[1][0][0] == 0) {
        for (int c = 0; c < 2; c++) {
            for (int r = 0; r < 256; r++) {
                byte rl_r = ((r * 2) % 256) + c;
                RL[c][r][0] = rl_r;
                RL[c][r][1] = SZ53P[rl_r] + (r >> 7);
            }
        }
    }
}

static void init_RLC() {
    init_SZ53P();
    if (RLC[255][0] == 0) {
        for (int r = 0; r < 256; r++) {
            byte rlc_r = r / 0x80 + ((r * 2) & 0xFF);
            RLC[r][0] = rlc_r;
            RLC[r][1] = SZ53P[rlc_r] + (r >> 7);
        }
    }
}

static void init_RR() {
    init_SZ53P();
    if (RR[1][0][0] == 0) {
        for (int c = 0; c < 2; c++) {
            for (int r = 0; r < 256; r++) {
                byte rr_r = c * 0x80 + (r / 2);
                RR[c][r][0] = rr_r;
                RR[c][r][1] = SZ53P[rr_r] + (r & 1);
            }
        }
    }
}

static void init_RRC() {
    init_SZ53P();
    if (RRC[255][0] == 0) {
        for (int r = 0; r < 256; r++) {
            byte rrc_r = ((r << 7) & 0xFF) + r / 2;
            RRC[r][0] = rrc_r;
            RRC[r][1] = SZ53P[rrc_r] + (r & 1);
        }
    }
}

static void init_RLA() {
    if (RLA[1][0][0] == 0) {
        for (int a = 0; a < 256; a++) {
            for (int f = 0; f < 256; f++) {
                byte rl_a = ((a * 2) % 256) + (f & 0x01);
                RLA[a][f][0] = rl_a;
                RLA[a][f][1] = (
                    (f & 0xC4)      // SZ.H.PN.
                    + (rl_a & 0x28) // ..5.3...
                    + (a >> 7)      // .......C
                );
            }
        }
    }
}

static void init_RLCA() {
    if (RLCA[1][0][0] == 0) {
        for (int a = 0; a < 256; a++) {
            for (int f = 0; f < 256; f++) {
                byte rlc_a = a / 0x80 + ((a * 2) & 0xFF);
                RLCA[a][f][0] = rlc_a;
                RLCA[a][f][1] = (
                    (f & 0xC4)       // SZ.H.PN.
                    + (rlc_a & 0x28) // ..5.3...
                    + (a >> 7)       // .......C
                );
            }
        }
    }
}

static void init_RRA() {
    if (RRA[1][0][0] == 0) {
        for (int a = 0; a < 256; a++) {
            for (int f = 0; f < 256; f++) {
                byte rr_a = (f & 0x01) * 0x80 + (a / 2);
                RRA[a][f][0] = rr_a;
                RRA[a][f][1] = (
                    (f & 0xC4)      // SZ.H.PN.
                    + (rr_a & 0x28) // ..5.3...
                    + (a & 1)       // .......C
                );
            }
        }
    }
}

static void init_RRCA() {
    if (RRCA[1][0][0] == 0) {
        for (int a = 0; a < 256; a++) {
            for (int f = 0; f < 256; f++) {
                byte rrc_a = ((a << 7) & 0xFF) + a / 2;
                RRCA[a][f][0] = rrc_a;
                RRCA[a][f][1] = (
                    (f & 0xC4)       // SZ.H.PN.
                    + (rrc_a & 0x28) // ..5.3...
                    + (a & 1)        // .......C
                );
            }
        }
    }
}

static void init_SBC() {
    if (1) {
        for (int c = 0; c < 2; c++) {
            for (int a = 0; a < 256; a++) {
                for (int i = 0; i < 256; i++) {
                    int v = a - c - i;
                    SBC[c][a][i][0] = v & 0xFF;
                    SBC[c][a][i][1] = (
                        (v & 0xA8)                                    // S.5.3...
                        + (((v & 0xFF) == 0) ? 0x40 : 0)              // .Z......
                        + (((a & 0x0F) - ((a - v) & 0x0F)) & 0x10)    // ...H....
                        + (((a ^ (a - v - c)) & (a ^ v) & 0x80) >> 5) // .....P..
                        + 0x02                                        // ......N.
                        + ((v < 0) ? 1 : 0)                           // .......C
                    );
                }
            }
        }
    }
}

static void init_SBC_A_A() {
    if (SBC_A_A[1][0][0] == 0) {
        for (int a = 0; a < 256; a++) {
            SBC_A_A[0][a][0] = 0x00;
            SBC_A_A[0][a][1] = 0x42;
            SBC_A_A[1][a][0] = 0xFF;
            SBC_A_A[1][a][1] = 0xBB;
        }
    }
}

static void init_SCF() {
    if (SCF[0][0] == 0) {
        for (int f = 0; f < 256; f++) {
            for (int a = 0; a < 256; a++) {
                SCF[f][a] = (
                    (f & 0xC4)   // SZ...PN.
                    + (a & 0x28) // ..5.3...
                    + 0x01       // ...H...C
                );
            }
        }
    }
}

static void init_SLA() {
    init_RL();
    if (SLA[1][0] == 0) {
        for (int r = 0; r < 256; r++) {
            SLA[r][0] = RL[0][r][0];
            SLA[r][1] = RL[0][r][1];
        }
    }
}

static void init_SLL() {
    init_RL();
    if (SLL[1][0] == 0) {
        for (int r = 0; r < 256; r++) {
            SLL[r][0] = RL[1][r][0];
            SLL[r][1] = RL[1][r][1];
        }
    }
}

static void init_SRA() {
    init_SZ53P();
    if (SRA[1][0] == 0) {
        for (int r = 0; r < 256; r++) {
            SRA[r][0] = (r & 0x80) + r / 2;
            SRA[r][1] = (
                SZ53P[(r & 0x80) + r / 2] // SZ5H3PN.
                + (r & 0x01)              // .......C
            );
        }
    }
}

static void init_SRL() {
    init_RR();
    if (SRL[2][0] == 0) {
        for (int r = 0; r < 256; r++) {
            SRL[r][0] = RR[0][r][0];
            SRL[r][1] = RR[0][r][1];
        }
    }
}

static void init_SUB() {
    init_SBC();
    if (SUB[0][1][0] == 0) {
        for (int a = 0; a < 256; a++) {
            for (int v = 0; v < 256; v++) {
                SUB[a][v][0] = SBC[0][a][v][0];
                SUB[a][v][1] = SBC[0][a][v][1];
            }
        }
    }
}

static void init_XOR() {
    init_SZ53P();
    if (XOR[1][0][0] == 0) {
        for (int a = 0; a < 256; a++) {
            for (int n = 0; n < 256; n++) {
                XOR[a][n][0] = a ^ n;
                XOR[a][n][1] = SZ53P[a ^ n];
            }
        }
    }
}

#ifdef CONTENTION
static void init_DELAYS_48K() {
    for (unsigned row = 64; row < 256; row++) {
        for (unsigned i = 0; i < 16; i++) {
            unsigned t = row * 224 - 1 + i * 8;
            for (unsigned j = 0; j < 6; j++) {
                DELAYS_48K[t + j] = 6 - j;
            }
        }
    }
}

static void init_DELAYS_128K() {
    for (unsigned row = 63; row < 255; row++) {
        for (unsigned i = 0; i < 16; i++) {
            unsigned t = row * 228 - 3 + i * 8;
            for (unsigned j = 0; j < 6; j++) {
                DELAYS_128K[t + j] = 6 - j;
            }
        }
    }
}
#endif

static void init_lookup_tables() {
    init_ADC();
    init_ADC_A_A();
    init_ADD();
    init_AND();
    init_BIT();
    init_CCF();
    init_CP();
    init_CPL();
    init_DAA();
    init_DEC();
    init_INC();
    init_NEG();
    init_OR();
    init_RL();
    init_RLA();
    init_RLC();
    init_RLCA();
    init_RR();
    init_RRC();
    init_RRA();
    init_RRCA();
    init_SBC();
    init_SBC_A_A();
    init_SCF();
    init_SLA();
    init_SLL();
    init_SRA();
    init_SRL();
    init_SUB();
    init_XOR();
#ifdef CONTENTION
    init_DELAYS_48K();
    init_DELAYS_128K();
#endif
}

static void out7ffd(CSimulatorObject* self, byte value) {
    self->mem128[0] = self->roms[(value & 0x10) / 0x10];
    self->mem128[3] = self->banks[value & 0x07];
    self->out7ffd = value;
}

static int accept_interrupt(CSimulatorObject* self, unsigned prev_pc) {
    unsigned long long* reg = self->registers;
    byte* mem = self->memory;

    byte opcode = MEMGET(prev_pc);
    unsigned pc = REG(PC);
    if (opcode == 0xFB || ((opcode == 0xDD || opcode == 0xFD) && prev_pc == (pc - 1) % 65536)) {
        return 0;
    }
    unsigned iaddr = 56;
    if (REG(IM) == 2) {
        unsigned vaddr = 255 + 256 * REG(I);
        iaddr = MEMGET(vaddr) + 256 * MEMGET((vaddr + 1) % 65536);
        REG(T) += 19;
    } else {
        REG(T) += 13;
    }
    unsigned sp = (REG(12) - 2) % 65536;
    REG(SP) = sp;
    if (sp > 0x3FFF) {
        MEMSET(sp, pc % 256);
    }
    sp = (sp + 1) % 65536;
    if (sp > 0x3FFF) {
        MEMSET(sp, pc / 256);
    }
    INC_R(1);
    REG(PC) = iaddr;
    REG(IFF) = 0;
    REG(HALT) = 0;
    return 1;
}

#ifdef CONTENTION
static void contend_48k(unsigned* t, unsigned* delay, int urc, int n, ...) {
    va_list ptr;

    va_start(ptr, n);
    for (int i = 0; i < n; i += 2) {
        unsigned address = va_arg(ptr, unsigned);
        unsigned tstates = va_arg(ptr, unsigned);
        if (tstates) {
            if (0x4000 <= address && address < 0x8000) {
                *delay += DELAYS_48K[*t];
                *t += DELAYS_48K[*t];
            }
            *t += tstates;
        } else {
            // I/O contention
            if (address & 1) {
                if (0x4000 <= address && address < 0x8000) {
                    contend_48k(t, delay, urc, 8, 0x4000, 1, 0x4000, 1, 0x4000, 1, 0x4000, 1);
                } else {
                    contend_48k(t, delay, urc, 2, 0, 4);
                }
            } else if (0x4000 <= address && address < 0x8000) {
                contend_48k(t, delay, urc, 4, 0x4000, 1, 0x4000, 3);
            } else {
                contend_48k(t, delay, urc, 4, 0, 1, 0x4000, 3);
            }
        }
    }
    va_end(ptr);
}

static void contend_128k(unsigned* t, unsigned* delay, int urc, int n, ...) {
    va_list ptr;

    va_start(ptr, n);
    for (int i = 0; i < n; i += 2) {
        unsigned address = va_arg(ptr, unsigned);
        unsigned tstates = va_arg(ptr, unsigned);
        if (tstates) {
            if ((0x4000 <= address && address < 0x8000) || (urc && address >= 0xC000)) {
                *delay += DELAYS_128K[*t];
                *t += DELAYS_128K[*t];
            }
            *t += tstates;
        } else {
            // I/O contention
            if (address & 1) {
                if ((0x4000 <= address && address < 0x8000) || (urc && address >= 0xC000)) {
                    contend_128k(t, delay, urc, 8, 0x4000, 1, 0x4000, 1, 0x4000, 1, 0x4000, 1);
                } else {
                    contend_128k(t, delay, urc, 2, 0, 4);
                }
            } else if ((0x4000 <= address && address < 0x8000) || (urc && address >= 0xC000)) {
                contend_128k(t, delay, urc, 4, 0x4000, 1, 0x4000, 3);
            } else {
                contend_128k(t, delay, urc, 4, 0, 1, 0x4000, 3);
            }
        }
    }
    va_end(ptr);
}
#endif

/*****************************************************************************/

/* ADD A,(HL) / AND (HL) / CP (HL) / OR (HL) / SUB (HL) / XOR (HL) */
static void af_hl(CSimulatorObject* self, void* lookup, int args[]) {
    byte (*table)[256][2] = lookup;
    unsigned long long* reg = self->registers;
    byte* mem = self->memory;

    unsigned old_a = REG(A);
    unsigned hl = REG(L) + 256 * REG(H);
#ifdef CONTENTION
    CONTEND {
        CPATTERN(4, REG(PC), 4, hl, 3);
    }
#endif
    REG(A) = table[old_a][MEMGET(hl)][0];
    REG(F) = table[old_a][MEMGET(hl)][1];

    INC_R(1);
    INC_T(7);
    INC_PC(1);
}

/* ADD A,n / AND n / CP n / OR n / SUB n / XOR n */
static void af_n(CSimulatorObject* self, void* lookup, int args[]) {
    byte (*table)[256][2] = lookup;
    unsigned long long* reg = self->registers;
    byte* mem = self->memory;

#ifdef CONTENTION
    CONTEND {
        unsigned pc = REG(PC);
        CPATTERN(4, pc, 4, (pc + 1) % 65536, 3);
    }
#endif
    unsigned old_a = REG(A);
    byte n = MEMGET((REG(PC) + 1) % 65536);
    REG(A) = table[old_a][n][0];
    REG(F) = table[old_a][n][1];

    INC_R(1);
    INC_T(7);
    INC_PC(2);
}

/* ADD A,r / AND r / CP r / OR r / SUB r / XOR r / CPL / DAA / RLA / RLCA / RRA / RRCA */
static void af_r(CSimulatorObject* self, void* lookup, int args[]) {
    byte (*table)[256][2] = lookup;
    int r_inc = args[0];
    int timing = args[1];
    int size = args[2];
    int r = args[3];
    unsigned long long* reg = self->registers;

#ifdef CONTENTION
    CONTEND {
        unsigned pc = REG(PC);
        if (size == 1) {
            CPATTERN(2, pc, 4);
        } else {
            CPATTERN(4, pc, 4, (pc + 1) % 65536, 4);
        }
    }
#endif
    unsigned old_a = REG(A);
    unsigned old_r = REG(r);
    REG(A) = table[old_a][old_r][0];
    REG(F) = table[old_a][old_r][1];

    INC_R(r_inc);
    INC_T(timing);
    INC_PC(size);
}

/* ADD A,(IX/Y+d) / AND (IX/Y+d) / CP (IX/Y+d) / OR (IX/Y+d) / SUB (IX/Y+d) / XOR (IX/Y+d) */
static void af_xy(CSimulatorObject* self, void* lookup, int args[]) {
    byte (*table)[256][2] = lookup;
    int xyh = args[0];
    int xyl = args[1];
    unsigned long long* reg = self->registers;
    byte* mem = self->memory;

    int xy = REG(xyl) + 256 * REG(xyh);
    int d = MEMGET((REG(PC) + 2) % 65536);
    int addr = (xy + (d < 128 ? d : d - 256)) % 65536;
#ifdef CONTENTION
    CONTEND {
        unsigned pc = REG(PC);
        unsigned pc2 = (pc + 2) % 65536;
        CPATTERN(18, pc, 4, (pc + 1) % 65536, 4, pc2, 3, pc2, 1, pc2, 1, pc2, 1, pc2, 1, pc2, 1, addr, 3);
    }
#endif
    unsigned old_a = REG(A);
    REG(A) = table[old_a][MEMGET(addr)][0];
    REG(F) = table[old_a][MEMGET(addr)][1];

    INC_R(2);
    INC_T(19);
    INC_PC(3);
}

/* ADC/SBC A,(HL) */
static void afc_hl(CSimulatorObject* self, void* lookup, int args[]) {
    byte (*table)[256][256][2] = lookup;
    unsigned long long* reg = self->registers;
    byte* mem = self->memory;

    unsigned old_a = REG(A);
    unsigned hl = REG(L) + 256 * REG(H);
#ifdef CONTENTION
    CONTEND {
        CPATTERN(4, REG(PC), 4, hl, 3);
    }
#endif
    REG(A) = table[REG(F) & 1][old_a][MEMGET(hl)][0];
    REG(F) = table[REG(F) & 1][old_a][MEMGET(hl)][1];

    INC_R(1);
    INC_T(7);
    INC_PC(1);
}

/* ADC/SBC A,n */
static void afc_n(CSimulatorObject* self, void* lookup, int args[]) {
    byte (*table)[256][256][2] = lookup;
    unsigned long long* reg = self->registers;
    byte* mem = self->memory;

#ifdef CONTENTION
    CONTEND {
        unsigned pc = REG(PC);
        CPATTERN(4, pc, 4, (pc + 1) % 65536, 3);
    }
#endif
    unsigned n = MEMGET((REG(PC) + 1) % 65536);
    unsigned old_a = REG(A);
    REG(A) = table[REG(F) & 1][old_a][n][0];
    REG(F) = table[REG(F) & 1][old_a][n][1];

    INC_R(1);
    INC_T(7);
    INC_PC(2);
}

/* ADC/SBC A,r (r != A) */
static void afc_r(CSimulatorObject* self, void* lookup, int args[]) {
    byte (*table)[256][256][2] = lookup;
    int r_inc = args[0];
    int timing = args[1];
    int size = args[2];
    int r = args[3];
    unsigned long long* reg = self->registers;

#ifdef CONTENTION
    CONTEND {
        unsigned pc = REG(PC);
        if (size == 1) {
            CPATTERN(2, pc, 4);
        } else {
            CPATTERN(4, pc, 4, (pc + 1) % 65536, 4);
        }
    }
#endif
    unsigned old_a = REG(A);
    REG(A) = table[REG(F) & 1][old_a][REG(r)][0];
    REG(F) = table[REG(F) & 1][old_a][REG(r)][1];

    INC_R(r_inc);
    INC_T(timing);
    INC_PC(size);
}

/* ADC/SBC A,(IX/Y+d) */
static void afc_xy(CSimulatorObject* self, void* lookup, int args[]) {
    byte (*table)[256][256][2] = lookup;
    int xyh = args[0];
    int xyl = args[1];
    unsigned long long* reg = self->registers;
    byte* mem = self->memory;

    int xy = REG(xyl) + 256 * REG(xyh);
    int d = MEMGET((REG(PC) + 2) % 65536);
    int addr = (xy + (d < 128 ? d : d - 256)) % 65536;
#ifdef CONTENTION
    CONTEND {
        unsigned pc = REG(PC);
        unsigned pc2 = (pc + 2) % 65536;
        CPATTERN(18, pc, 4, (pc + 1) % 65536, 4, pc2, 3, pc2, 1, pc2, 1, pc2, 1, pc2, 1, pc2, 1, addr, 3);
    }
#endif
    unsigned old_a = REG(A);
    REG(A) = table[REG(F) & 1][old_a][MEMGET(addr)][0];
    REG(F) = table[REG(F) & 1][old_a][MEMGET(addr)][1];

    INC_R(2);
#ifdef CONTENTION
    INC_T(19);
#else
    INC_T(19);
#endif
    INC_PC(3);
}

/* RLC/RRC/SLA/SLL/SRA/SRL (HL) */
static void f_hl(CSimulatorObject* self, void* lookup, int args[]) {
    byte (*table)[2] = lookup;
    unsigned long long* reg = self->registers;
    byte* mem = self->memory;

    unsigned hl = REG(L) + 256 * REG(H);
#ifdef CONTENTION
    CONTEND {
        unsigned pc = REG(PC);
        CPATTERN(10, pc, 4, (pc + 1) % 65536, 4, hl, 3, hl, 1, hl, 3);
    }
#endif
    REG(F) = table[MEMGET(hl)][1];
    if (hl > 0x3FFF) {
        MEMSET(hl, table[MEMGET(hl)][0]);
    }

    INC_R(2);
    INC_T(15);
    INC_PC(2);
}

/* RLC/RRC/SLA/SLL/SRA/SRL r */
static void f_r(CSimulatorObject* self, void* lookup, int args[]) {
    byte (*table)[2] = lookup;
    int r = args[0];
    unsigned long long* reg = self->registers;

#ifdef CONTENTION
    CONTEND {
        unsigned pc = REG(PC);
        CPATTERN(4, pc, 4, (pc + 1) % 65536, 4);
    }
#endif
    unsigned old_r = REG(r);
    REG(r) = table[old_r][0];
    REG(F) = table[old_r][1];

    INC_R(2);
    INC_T(8);
    INC_PC(2);
}

/* RLC/RRC/SLA/SLL/SRA/SRL (IX/Y+d)[,r] */
static void f_xy(CSimulatorObject* self, void* lookup, int args[]) {
    byte (*table)[2] = lookup;
    int xyh = args[0];
    int xyl = args[1];
    int dest = args[2];
    unsigned long long* reg = self->registers;
    byte* mem = self->memory;

    int xy = REG(xyl) + 256 * REG(xyh);
    int d = MEMGET((REG(PC) + 2) % 65536);
    int addr = (xy + (d < 128 ? d : d - 256)) % 65536;
#ifdef CONTENTION
    CONTEND {
        unsigned pc = REG(PC);
        unsigned pc3 = (pc + 3) % 65536;
        CPATTERN(18, pc, 4, (pc + 1) % 65536, 4, (pc + 2) % 65536, 3, pc3, 3, pc3, 1, pc3, 1, addr, 3, addr, 1, addr, 3);
    }
#endif
    byte value = table[MEMGET(addr)][0];
    REG(F) = table[MEMGET(addr)][1];
    if (addr > 0x3FFF) {
        MEMSET(addr, value);
    }
    if (dest >= 0) {
        REG(dest) = value;
    }

    INC_R(2);
    INC_T(23);
    INC_PC(4);
}

/* DEC/INC/RL/RR (HL) */
static void fc_hl(CSimulatorObject* self, void* lookup, int args[]) {
    byte (*table)[256][2] = lookup;
    int r_inc = args[0];
    int timing = args[1];
    int size = args[2];
    unsigned long long* reg = self->registers;
    byte* mem = self->memory;

    unsigned hl = REG(L) + 256 * REG(H);
#ifdef CONTENTION
    CONTEND {
        unsigned pc = REG(PC);
        if (size == 2) {
            CPATTERN(10, pc, 4, (pc + 1) % 65536, 4, hl, 3, hl, 1, hl, 3);
        } else {
            CPATTERN(8, pc, 4, hl, 3, hl, 1, hl, 3);
        }
    }
#endif
    unsigned cf = REG(F) & 1;
    REG(F) = table[cf][MEMGET(hl)][1];
    if (hl > 0x3FFF) {
        MEMSET(hl, table[cf][MEMGET(hl)][0]);
    }

    INC_R(r_inc);
    INC_T(timing);
    INC_PC(size);
}

/* DEC/INC/RL/RR r / ADC A,A / SBC A,A */
static void fc_r(CSimulatorObject* self, void* lookup, int args[]) {
    byte (*table)[256][2] = lookup;
    int r_inc = args[0];
    int timing = args[1];
    int size = args[2];
    int r = args[3];
    unsigned long long* reg = self->registers;

#ifdef CONTENTION
    CONTEND {
        unsigned pc = REG(PC);
        if (size == 1) {
            CPATTERN(2, pc, 4);
        } else {
            CPATTERN(4, pc, 4, (pc + 1) % 65536, 4);
        }
    }
#endif
    byte old_r = REG(r);
    REG(r) = table[REG(F) % 2][old_r][0];
    REG(F) = table[REG(F) % 2][old_r][1];

    INC_R(r_inc);
    INC_T(timing);
    INC_PC(size);
}

/* DEC/INC/RL/RR (IX/Y+d)[,r] */
static void fc_xy(CSimulatorObject* self, void* lookup, int args[]) {
    byte (*table)[256][2] = lookup;
    int size = args[0];
    int xyh = args[1];
    int xyl = args[2];
    int dest = args[3];
    unsigned long long* reg = self->registers;
    byte* mem = self->memory;

    int xy = REG(xyl) + 256 * REG(xyh);
    int d = MEMGET((REG(PC) + 2) % 65536);
    int addr = (xy + (d < 128 ? d : d - 256)) % 65536;
#ifdef CONTENTION
    CONTEND {
        unsigned pc = REG(PC);
        unsigned pc2 = (pc + 2) % 65536;
        unsigned pc3 = (pc + 3) % 65536;
        if (size == 3) {
            CPATTERN(22, pc, 4, (pc + 1) % 65536, 4, pc2, 3, pc2, 1, pc2, 1, pc2, 1, pc2, 1, pc2, 1, addr, 3, addr, 1, addr, 3);
        } else {
            CPATTERN(18, pc, 4, (pc + 1) % 65536, 4, pc2, 3, pc3, 3, pc3, 1, pc3, 1, addr, 3, addr, 1, addr, 3);
        }
    }
#endif
    int value = table[REG(F) & 1][MEMGET(addr)][0];
    REG(F) = table[REG(F) & 1][MEMGET(addr)][1];
    if (addr > 0x3FFF) {
        MEMSET(addr, value);
    }
    if (dest >= 0) {
        REG(dest) = value;
    }

    INC_R(2);
    INC_T(23);
    INC_PC(size);
}

/* ADC HL,BC/DE/HL/SP */
static void adc_hl(CSimulatorObject* self, void* lookup, int args[]) {
    unsigned rh = args[0];
    unsigned rl = args[1];
    unsigned long long* reg = self->registers;

#ifdef CONTENTION
    CONTEND {
        unsigned pc = REG(PC);
        unsigned ir = REG(R) + 256 * REG(I);
        CPATTERN(18, pc, 4, (pc + 1) % 65536, 4, ir, 1, ir, 1, ir, 1, ir, 1, ir, 1, ir, 1, ir, 1);
    }
#endif
    unsigned rr = REG(rl) + 256 * REG(rh);
    unsigned hl = REG(L) + 256 * REG(H);
    unsigned rr_c = rr + (REG(F) & 1);
    unsigned result = hl + rr_c;
    unsigned f = 0;
    if (result > 0xFFFF) {
        result %= 65536;
        f = 0x01; // .......C
    }
    if (result == 0) {
        f += 0x40; // .Z......
    }
    if ((hl % 4096) + (rr_c % 4096) > 0x0FFF) {
        f += 0x10; // ...H....
    }
    if ((hl ^ rr) < 0x8000 && (hl ^ result) > 0x7FFF) {
        // Augend and addend signs are the same - overflow if their sign
        // differs from the sign of the result
        f += 0x04; // .....P..
    }
    unsigned h = result / 256;
    REG(F) = f + (h & 0xA8);
    REG(L) = result % 256;
    REG(H) = h;

    INC_R(2);
    INC_T(15);
    INC_PC(2);
}

/* ADD HL/IX/IY,BC/DE/HL/SP/IX/IY */
static void add_rr(CSimulatorObject* self, void* lookup, int args[]) {
    int r_inc = args[0];
    int timing = args[1];
    int size = args[2];
    int ah = args[3];
    int al = args[4];
    int rh = args[5];
    int rl = args[6];
    unsigned long long* reg = self->registers;

#ifdef CONTENTION
    CONTEND {
        unsigned pc = REG(PC);
        unsigned ir = REG(R) + 256 * REG(I);
        if (size == 1) {
            CPATTERN(16, pc, 4, ir, 1, ir, 1, ir, 1, ir, 1, ir, 1, ir, 1, ir, 1);
        } else {
            CPATTERN(18, pc, 4, (pc + 1) % 65536, 4, ir, 1, ir, 1, ir, 1, ir, 1, ir, 1, ir, 1, ir, 1);
        }
    }
#endif
    unsigned addend_v = REG(rl) + 256 * REG(rh);
    unsigned augend_v = REG(al) + 256 * REG(ah);
    unsigned result = augend_v + addend_v;
    unsigned f = REG(F) & 0xC4; // SZ...P..
    if (result > 0xFFFF) {
        result %= 65536;
        f += 0x01; // .......C
    }
    if ((augend_v % 4096) + (addend_v % 4096) > 0x0FFF) {
        f += 0x10; // ...H....
    }
    unsigned result_hi = result / 256;
    REG(F) = f + (result_hi & 0x28);
    REG(al) = result % 256;
    REG(ah) = result_hi;

    INC_R(r_inc);
    INC_T(timing);
    INC_PC(size);
}

/* BIT n,(HL) */
static void bit_hl(CSimulatorObject* self, void* lookup, int args[]) {
    int b = args[0];
    unsigned long long* reg = self->registers;
    byte* mem = self->memory;

    unsigned hl = REG(L) + 256 * REG(H);
#ifdef CONTENTION
    CONTEND {
        unsigned pc = REG(PC);
        CPATTERN(8, pc, 4, (pc + 1) % 65536, 4, hl, 3, hl, 1);
    }
#endif
    REG(F) = BIT[REG(F) & 1][b][MEMGET(hl)];

    INC_R(2);
    INC_T(12);
    INC_PC(2);
}

/* BIT n,r */
static void bit_r(CSimulatorObject* self, void* lookup, int args[]) {
    int b = args[0];
    int r = args[1];
    unsigned long long* reg = self->registers;

#ifdef CONTENTION
    CONTEND {
        unsigned pc = REG(PC);
        CPATTERN(4, pc, 4, (pc + 1) % 65536, 4);
    }
#endif
    REG(F) = BIT[REG(F) & 1][b][REG(r)];

    INC_R(2);
    INC_T(8);
    INC_PC(2);
}

/* BIT n,(IX/Y+d) */
static void bit_xy(CSimulatorObject* self, void* lookup, int args[]) {
    int b = args[0];
    int xyh = args[1];
    int xyl = args[2];
    unsigned long long* reg = self->registers;
    byte* mem = self->memory;

    int xy = REG(xyl) + 256 * REG(xyh);
    int d = MEMGET((REG(PC) + 2) % 65536);
    int addr = (xy + (d < 128 ? d : d - 256)) % 65536;
#ifdef CONTENTION
    CONTEND {
        unsigned pc = REG(PC);
        unsigned pc3 = (pc + 3) % 65536;
        CPATTERN(16, pc, 4, (pc + 1) % 65536, 4, (pc + 2) % 65536, 3, pc3, 3, pc3, 1, pc3, 1, addr, 3, addr, 1);
    }
#endif
    byte value = BIT[REG(F) & 1][b][MEMGET(addr)];
    REG(F) = (value & 0xD7) + ((xy / 256) & 0x28);

    INC_R(2);
    INC_T(20);
    INC_PC(4);
}

/* CALL nn / CALL cc,nn */
static void call(CSimulatorObject* self, void* lookup, int args[]) {
    unsigned c_and = args[0];
    unsigned c_val = args[1];
    unsigned long long* reg = self->registers;

    if (c_and && (REG(F) & c_and) == c_val) {
#ifdef CONTENTION
        CONTEND {
            unsigned pc = REG(PC);
            CPATTERN(6, pc, 4, (pc + 1) % 65536, 3, (pc + 2) % 65536, 3);
        }
#endif
        INC_T(10);
        INC_PC(3);
    } else {
        byte* mem = self->memory;
        unsigned pc = REG(PC);
        REG(PC) = MEMGET((pc + 1) % 65536) + 256 * MEMGET((pc + 2) % 65536);
        unsigned ret_addr = (pc + 3) % 65536;
        unsigned sp = (REG(SP) - 2) % 65536;
        REG(SP) = sp;
        if (sp > 0x3FFF) {
            MEMSET(sp, ret_addr % 256);
        }
        sp = (sp + 1) % 65536;
        if (sp > 0x3FFF) {
            MEMSET(sp, ret_addr / 256);
        }
#ifdef CONTENTION
        CONTEND {
            unsigned pc2 = (pc + 2) % 65536;
            CPATTERN(12, pc, 4, (pc + 1) % 65536, 3, pc2, 3, pc2, 1, sp, 3, (sp - 1) % 65536, 3);
        }
#endif
        INC_T(17);
    }

    INC_R(1);
}

/* CCF / SCF */
static void cf(CSimulatorObject* self, void* lookup, int args[]) {
    byte (*table)[256] = lookup;
    unsigned long long* reg = self->registers;

#ifdef CONTENTION
    CONTEND {
        CPATTERN(2, REG(PC), 4);
    }
#endif
    REG(F) = table[REG(F)][REG(A)];

    INC_R(1);
    INC_T(4);
    INC_PC(1);
}

/* CPI / CPD / CPIR / CPDR */
static void cpi(CSimulatorObject* self, void* lookup, int args[]) {
    int inc = args[0];
    int repeat = args[1];
    unsigned long long* reg = self->registers;
    byte* mem = self->memory;

    unsigned hl = REG(L) + 256 * REG(H);
    unsigned bc = REG(C) + 256 * REG(B);
    unsigned a = REG(A);
    unsigned value = MEMGET(hl);
    hl = (hl + inc) % 65536;
    bc = (bc - 1) % 65536;
    REG(L) = hl % 256;
    REG(H) = hl / 256;
    REG(C) = bc % 256;
    REG(B) = bc / 256;
    int cp = a - value;
    int hf = a % 16 < value % 16;
    unsigned f = (cp & 0x80) + hf * 0x10 + 0x02 + (REG(F) % 2); // S..H..NC
    if (repeat && cp && bc) {
        REG(F) = f + ((REG(PC) / 256) & 0x28) + 0x04; // .Z5.3P..
#ifdef CONTENTION
        CONTEND {
            unsigned pc = REG(PC);
            hl = (hl - inc) % 65536;
            CPATTERN(26, pc, 4, (pc + 1) % 65536, 4, hl, 3, hl, 1, hl, 1, hl, 1, hl, 1, hl, 1, hl, 1, hl, 1, hl, 1, hl, 1, hl, 1);
        }
#endif
        INC_T(21);
    } else {
        int n = cp - hf;
        REG(F) = f + (cp == 0) * 0x40 + (n & 0x02) * 16 + (n & 0x08) + (bc > 0) * 0x04; // .Z5.3P..
#ifdef CONTENTION
        CONTEND {
            unsigned pc = REG(PC);
            hl = (hl - inc) % 65536;
            CPATTERN(16, pc, 4, (pc + 1) % 65536, 4, hl, 3, hl, 1, hl, 1, hl, 1, hl, 1, hl, 1);
        }
#endif
        INC_T(16);
        INC_PC(2);
    }

    INC_R(2);
}

/* DI / EI */
static void di_ei(CSimulatorObject* self, void* lookup, int args[]) {
    int iff = args[0];
    unsigned long long* reg = self->registers;

#ifdef CONTENTION
    CONTEND {
        CPATTERN(2, REG(PC), 4);
    }
#endif
    REG(IFF) = iff;

    INC_R(1);
    INC_T(4);
    INC_PC(1);
}

/* DJNZ nn */
static void djnz(CSimulatorObject* self, void* lookup, int args[]) {
    unsigned long long* reg = self->registers;

    unsigned b = (REG(B) - 1) % 256;
    REG(B) = b;
    if (b) {
#ifdef CONTENTION
        CONTEND {
            unsigned pc = REG(PC);
            unsigned pc1 = (pc + 1) % 65536;
            CPATTERN(16, pc, 4, REG(R) + 256 * REG(I), 1, pc1, 3, pc1, 1, pc1, 1, pc1, 1, pc1, 1, pc1, 1);
        }
#endif
        INC_T(13);
        unsigned pc = REG(PC);
        byte* mem = self->memory;
        int offset = MEMGET((pc + 1) % 65536);
        REG(PC) = (pc + (offset < 128 ? offset + 2 : offset - 254)) % 65536;
    } else {
#ifdef CONTENTION
        CONTEND {
            unsigned pc = REG(PC);
            CPATTERN(6, pc, 4, REG(R) + 256 * REG(I), 1, (pc + 1) % 65536, 3);
        }
#endif
        INC_T(8);
        INC_PC(2);
    }

    INC_R(1);
}

/* EX AF,AF' */
static void ex_af(CSimulatorObject* self, void* lookup, int arg[]) {
    unsigned long long* reg = self->registers;

#ifdef CONTENTION
    CONTEND {
        CPATTERN(2, REG(PC), 4);
    }
#endif
    unsigned a = REG(A);
    unsigned f = REG(F);
    REG(A) = REG(xA);
    REG(F) = REG(xF);
    REG(xA) = a;
    REG(xF) = f;

    INC_R(1);
    INC_T(4);
    INC_PC(1);
}

/* EX DE,HL */
static void ex_de_hl(CSimulatorObject* self, void* lookup, int arg[]) {
    unsigned long long* reg = self->registers;

#ifdef CONTENTION
    CONTEND {
        CPATTERN(2, REG(PC), 4);
    }
#endif
    unsigned d = REG(D);
    unsigned e = REG(E);
    REG(D) = REG(H);
    REG(E) = REG(L);
    REG(H) = d;
    REG(L) = e;

    INC_R(1);
    INC_T(4);
    INC_PC(1);
}

/* EX (SP),HL/IX/IY */
static void ex_sp(CSimulatorObject* self, void* lookup, int args[]) {
    int r_inc = args[0];
    int timing = args[1];
    int size = args[2];
    int rh = args[3];
    int rl = args[4];
    unsigned long long* reg = self->registers;
    byte* mem = self->memory;

    unsigned sp = REG(SP);
#ifdef CONTENTION
    CONTEND {
        unsigned pc = REG(PC);
        unsigned spn = (sp + 1) % 65536;
        if (size == 1) {
            CPATTERN(16, pc, 4, sp, 3, spn, 3, spn, 1, spn, 3, sp, 3, sp, 1, sp, 1);
        } else {
            CPATTERN(18, pc, 4, (pc + 1) % 65536, 4, sp, 3, spn, 3, spn, 1, spn, 3, sp, 3, sp, 1, sp, 1);
        }
    }
#endif
    byte sp1 = MEMGET(sp);
    if (sp > 0x3FFF) {
        MEMSET(sp, REG(rl));
    }
    sp = (sp + 1) % 65536;
    byte sp2 = MEMGET(sp);
    if (sp > 0x3FFF) {
        MEMSET(sp, REG(rh));
    }
    REG(rl) = sp1;
    REG(rh) = sp2;

    INC_R(r_inc);
    INC_T(timing);
    INC_PC(size);
}

/* EXX */
static void exx(CSimulatorObject* self, void* lookup, int args[]) {
    unsigned long long* reg = self->registers;

#ifdef CONTENTION
    CONTEND {
        CPATTERN(2, REG(PC), 4);
    }
#endif
    unsigned b = REG(B);
    unsigned c = REG(C);
    unsigned d = REG(D);
    unsigned e = REG(E);
    unsigned h = REG(H);
    unsigned l = REG(L);
    REG(B) = REG(xB);
    REG(C) = REG(xC);
    REG(D) = REG(xD);
    REG(E) = REG(xE);
    REG(H) = REG(xH);
    REG(L) = REG(xL);
    REG(xB) = b;
    REG(xC) = c;
    REG(xD) = d;
    REG(xE) = e;
    REG(xH) = h;
    REG(xL) = l;

    INC_R(1);
    INC_T(4);
    INC_PC(1);
}

/* HALT */
static void halt(CSimulatorObject* self, void* lookup, int args[]) {
    unsigned long long* reg = self->registers;

#ifdef CONTENTION
    CONTEND {
        CPATTERN(2, (REG(PC) + REG(HALT)) % 65536, 4);
    }
#endif
    INC_T(4);
    if (REG(IFF) && (REG(T) % self->frame_duration) < self->int_active) {
        INC_PC(1);
        REG(HALT) = 0;
    } else {
        REG(HALT) = 1;
    }

    INC_R(1);
}

/* IM 0/1/2 */
static void im(CSimulatorObject* self, void* lookup, int args[]) {
    int mode = args[0];
    unsigned long long* reg = self->registers;

#ifdef CONTENTION
    CONTEND {
        unsigned pc = REG(PC);
        CPATTERN(4, pc, 4, (pc + 1) % 65536, 4);
    }
#endif
    REG(IM) = mode;

    INC_R(2);
    INC_T(8);
    INC_PC(2);
}

/* IN A,(n) */
static void in_a(CSimulatorObject* self, void* lookup, int args[]) {
    unsigned long long* reg = self->registers;

#ifdef CONTENTION
    CONTEND {
        byte* mem = self->memory;
        unsigned pc = REG(PC);
        unsigned pc1 = (pc + 1) % 65536;
        unsigned port = MEMGET(pc1) + 256 * REG(A);
        CPATTERN(6, pc, 4, pc1, 3, port, 0);
    }
#endif
    unsigned value = 255;
    if (self->in_a_n_tracer) {
        byte* mem = self->memory;
        unsigned port = MEMGET((REG(PC) + 1) % 65536) + 256 * REG(A);
        PyObject* args = Py_BuildValue("(I)", port);
        PyObject* rv = PyObject_CallObject(self->in_a_n_tracer, args);
        Py_XDECREF(args);
        if (rv) {
            value = PyLong_AsLong(rv);
            Py_DECREF(rv);
        }
    }
    REG(A) = value;

    INC_R(1);
    INC_T(11);
    INC_PC(2);
}

/* IN r,(C) */
static void in_c(CSimulatorObject* self, void* lookup, int args[]) {
    int r = args[0];
    unsigned long long* reg = self->registers;

#ifdef CONTENTION
    CONTEND {
        unsigned pc = REG(PC);
        unsigned port = REG(C) + 256 * REG(B);
        CPATTERN(6, pc, 4, (pc + 1) % 65536, 4, port, 0);
    }
#endif
    unsigned value = 255;
    if (self->in_r_c_tracer) {
        unsigned port = REG(C) + 256 * REG(B);
        PyObject* args = Py_BuildValue("(I)", port);
        PyObject* rv = PyObject_CallObject(self->in_a_n_tracer, args);
        Py_XDECREF(args);
        if (rv) {
            value = PyLong_AsLong(rv);
            Py_DECREF(rv);
        }
    }
    if (r != F) {
        REG(r) = value;
    }
    REG(F) = SZ53P[value] + (REG(F) & 1);

    INC_R(2);
    INC_T(12);
    INC_PC(2);
}

/* INC/DEC BC/DE/HL/SP/IX/IY */
static void inc_dec_rr(CSimulatorObject* self, void* lookup, int args[]) {
    int r_inc = args[0];
    int timing = args[1];
    int size = args[2];
    int inc = args[3];
    int rh = args[4];
    int rl = args[5];
    unsigned long long* reg = self->registers;

#ifdef CONTENTION
    CONTEND {
        unsigned pc = REG(PC);
        unsigned ir = REG(R) + 256 * REG(I);
        if (size == 1) {
            CPATTERN(6, pc, 4, ir, 1, ir, 1);
        } else {
            CPATTERN(8, pc, 4, (pc + 1) % 65536, 4, ir, 1, ir, 1);
        }
    }
#endif
    if (rl == SP) {
        REG(SP) = (REG(SP) + inc) % 65536;
    } else {
        unsigned value = (REG(rl) + 256 * REG(rh) + inc) % 65536;
        REG(rh) = value / 256;
        REG(rl) = value % 256;
    }

    INC_R(r_inc);
    INC_T(timing);
    INC_PC(size);
}

/* INI / IND / INIR / INDR */
static void ini(CSimulatorObject* self, void* lookup, int args[]) {
    int inc = args[0];
    int repeat = args[1];
    unsigned long long* reg = self->registers;
    byte* mem = self->memory;

    unsigned hl = REG(L) + 256 * REG(H);
    unsigned b = REG(B);
    unsigned c = REG(C);
    byte value = 191;
    if (self->ini_tracer) {
        unsigned port = c + 256 * b;
        PyObject* args = Py_BuildValue("(I)", port);
        PyObject* rv = PyObject_CallObject(self->in_a_n_tracer, args);
        Py_XDECREF(args);
        if (rv) {
            value = (byte)PyLong_AsLong(rv);
            Py_DECREF(rv);
        }
    }
    if (hl > 0x3FFF) {
        MEMSET(hl, value);
    }
    b = (b - 1) % 256;
    hl = (hl + inc) % 65536;
    REG(L) = hl % 256;
    REG(H) = hl / 256;
    REG(B) = b;
    unsigned j = value + ((c + inc) % 256);
    unsigned n = (value & 0x80) / 64;
    int cf = j > 0xFF ? 1 : 0;
    if (repeat && b) {
        unsigned hf = 0;
        unsigned p = 0;
        if (cf) {
            if (n) {
                hf = (b % 16 == 0) * 0x10;
                p = PARITY[(j % 8) ^ b ^ ((b - 1) % 8)];
            } else {
                hf = ((b & 0x0F) == 0x0F) * 0x10;
                p = PARITY[(j % 8) ^ b ^ ((b + 1) % 8)];
            }
        } else {
            hf = 0;
            p = PARITY[(j % 8) ^ b ^ (b % 8)];
        }
        REG(F) = (b & 0x80) + ((REG(PC) >> 8) & 0x28) + hf + p + n + cf;
#ifdef CONTENTION
        CONTEND {
            unsigned pc = REG(PC);
            unsigned port = c + 256 * ((b + 1) % 256);
            unsigned ir = REG(R) + 256 * REG(I);
            hl = (hl - inc) % 65536;
            CPATTERN(20, pc, 4, (pc + 1) % 65536, 4, ir, 1, port, 0, hl, 3, hl, 1, hl, 1, hl, 1, hl, 1, hl, 1);
        }
#endif
        INC_T(21);
    } else {
        REG(F) = (b & 0xA8) + (b == 0) * 0x40 + cf * 0x11 + PARITY[(j % 8) ^ b] + n;
#ifdef CONTENTION
        CONTEND {
            unsigned pc = REG(PC);
            unsigned port = c + 256 * ((b + 1) % 256);
            unsigned ir = REG(R) + 256 * REG(I);
            hl = (hl - inc) % 65536;
            CPATTERN(10, pc, 4, (pc + 1) % 65536, 4, ir, 1, port, 0, hl, 3);
        }
#endif
        INC_PC(2);
        INC_T(16);
    }

    INC_R(2);
}

/* JP nn / JP cc,nn */
static void jp(CSimulatorObject* self, void* lookup, int args[]) {
    unsigned c_and = args[0];
    unsigned c_val = args[1];
    unsigned long long* reg = self->registers;

#ifdef CONTENTION
    CONTEND {
        unsigned pc = REG(PC);
        CPATTERN(6, pc, 4, (pc + 1) % 65536, 3, (pc + 2) % 65536, 3);
    }
#endif
    if ((REG(F) & c_and) == c_val) {
        byte* mem = self->memory;
        REG(PC) = MEMGET((REG(PC) + 1) % 65536) + 256 * MEMGET((REG(PC) + 2) % 65536);
    } else {
        INC_PC(3);
    }

    INC_R(1);

    INC_T(10);
}

/* JP (HL/IX/IY) */
static void jp_rr(CSimulatorObject* self, void* lookup, int args[]) {
    int r_inc = args[0];
    int timing = args[1];
    int rh = args[2];
    int rl = args[3];
    unsigned long long* reg = self->registers;

    INC_R(r_inc);
#ifdef CONTENTION
    CONTEND {
        unsigned pc = REG(PC);
        if (timing == 4) {
            CPATTERN(2, pc, 4);
        } else {
            CPATTERN(4, pc, 4, (pc + 1) % 65536, 4);
        }
    }
#endif
    INC_T(timing);
    REG(PC) = REG(rl) + 256 * REG(rh);
}

/* JR nn / JR cc,nn */
static void jr(CSimulatorObject* self, void* lookup, int args[]) {
    unsigned c_and = args[0];
    unsigned c_val = args[1];
    unsigned long long* reg = self->registers;

    if ((REG(F) & c_and) == c_val) {
#ifdef CONTENTION
        CONTEND {
            unsigned pc = REG(PC);
            unsigned pc1 = (pc + 1) % 65536;
            CPATTERN(14, pc, 4, pc1, 3, pc1, 1, pc1, 1, pc1, 1, pc1, 1, pc1, 1);
        }
#endif
        byte* mem = self->memory;
        byte offset = MEMGET((REG(PC) + 1) % 65536);
        INC_PC(offset < 128 ? offset + 2 : offset - 254);
        INC_T(12);
    } else {
#ifdef CONTENTION
        CONTEND {
            unsigned pc = REG(PC);
            CPATTERN(4, pc, 4, (pc + 1) % 65536, 3);
        }
#endif
        INC_PC(2);
        INC_T(7);
    }

    INC_R(1);
}

/* LD A,I/R */
static void ld_a_ir(CSimulatorObject* self, void* lookup, int args[]) {
    int r = args[0];
    unsigned long long* reg = self->registers;

#ifdef CONTENTION
    CONTEND {
        unsigned pc = REG(PC);
        CPATTERN(6, pc, 4, (pc + 1) % 65536, 4, REG(R) + 256 * REG(I), 1);
    }
#endif
    INC_R(2);
    unsigned a = REG(r);
    REG(A) = a;
    INC_T(9);
    if (REG(IFF) && (REG(T) % self->frame_duration) < self->int_active) {
        REG(F) = (a & 0xA8) + (a == 0) * 0x40 + (REG(F) & 1);
    } else {
        REG(F) = (a & 0xA8) + (a == 0) * 0x40 + REG(IFF) * 0x04 + (REG(F) & 1);
    }
    INC_PC(2);
}

/* LD (HL),n */
static void ld_hl_n(CSimulatorObject* self, void* lookup, int args[]) {
    unsigned long long* reg = self->registers;

    unsigned hl = REG(L) + 256 * REG(H);
#ifdef CONTENTION
    CONTEND {
        unsigned pc = REG(PC);
        CPATTERN(6, pc, 4, (pc + 1) % 65536, 3, hl, 3);
    }
#endif
    if (hl > 0x3FFF) {
        byte* mem = self->memory;
        MEMSET(hl, MEMGET((REG(PC) + 1) % 65536));
    }

    INC_R(1);
    INC_T(10);
    INC_PC(2);
}

/* LD r,n */
static void ld_r_n(CSimulatorObject* self, void* lookup, int args[]) {
    int r_inc = args[0];
    int timing = args[1];
    int size = args[2];
    int r = args[3];
    unsigned long long* reg = self->registers;
    byte* mem = self->memory;

#ifdef CONTENTION
    CONTEND {
        unsigned pc = REG(PC);
        if (size == 2) {
            CPATTERN(4, pc, 4, (pc + 1) % 65536, 3);
        } else {
            CPATTERN(6, pc, 4, (pc + 1) % 65536, 4, (pc + 2) % 65536, 3);
        }
    }
#endif
    REG(r) = MEMGET((REG(PC) + size - 1) % 65536);

    INC_R(r_inc);
    INC_T(timing);
    INC_PC(size);
}

/* LD r,r */
static void ld_r_r(CSimulatorObject* self, void* lookup, int args[]) {
    int r_inc = args[0];
    int timing = args[1];
    int size = args[2];
    int r1 = args[3];
    int r2 = args[4];
    unsigned long long* reg = self->registers;

#ifdef CONTENTION
    CONTEND {
        unsigned pc = REG(PC);
        if (size == 1) {
            CPATTERN(2, pc, 4);
        } else if (timing == 8) {
            // LD r,IXh/IXl/IYh/IYl / LD IXh/IXl/IYh/IYl,r
            CPATTERN(4, pc, 4, (pc + 1) % 65536, 4);
        } else {
            // LD I/R,A
            CPATTERN(6, pc, 4, (pc + 1) % 65536, 4, REG(R) + 256 * REG(I), 1);
        }
    }
#endif
    INC_R(r_inc);
    REG(r1) = REG(r2);
    INC_T(timing);
    INC_PC(size);
}

/* LD r,(HL/DE/BC) */
static void ld_r_rr(CSimulatorObject* self, void* lookup, int args[]) {
    int r = args[0];
    int rh = args[1];
    int rl = args[2];
    unsigned long long* reg = self->registers;
    byte* mem = self->memory;

#ifdef CONTENTION
    CONTEND {
        CPATTERN(4, REG(PC), 4, REG(rl) + 256 * REG(rh), 3);
    }
#endif
    REG(r) = MEMGET(REG(rl) + 256 * REG(rh));

    INC_R(1);
    INC_T(7);
    INC_PC(1);
}

/* LD (HL/DE/BC),r */
static void ld_rr_r(CSimulatorObject* self, void* lookup, int args[]) {
    int rh = args[0];
    int rl = args[1];
    int r = args[2];
    unsigned long long* reg = self->registers;

    unsigned addr = REG(rl) + 256 * REG(rh);
#ifdef CONTENTION
    CONTEND {
        CPATTERN(4, REG(PC), 4, addr, 3);
    }
#endif
    if (addr > 0x3FFF) {
        byte* mem = self->memory;
        MEMSET(addr, REG(r));
    }

    INC_R(1);
    INC_T(7);
    INC_PC(1);
}

/* LD r,(IX/Y+d) */
static void ld_r_xy(CSimulatorObject* self, void* lookup, int args[]) {
    int r = args[0];
    int xyh = args[1];
    int xyl = args[2];
    unsigned long long* reg = self->registers;
    byte* mem = self->memory;

    unsigned xy = REG(xyl) + 256 * REG(xyh);
    unsigned offset = MEMGET((REG(PC) + 2) % 65536);
    unsigned addr = (xy + (offset < 128 ? offset : offset - 256)) % 65536;
#ifdef CONTENTION
    CONTEND {
        unsigned pc = REG(PC);
        unsigned pc2 = (pc + 2) % 65536;
        CPATTERN(18, pc, 4, (pc + 1) % 65536, 4, pc2, 3, pc2, 1, pc2, 1, pc2, 1, pc2, 1, pc2, 1, addr, 3);
    }
#endif
    REG(r) = MEMGET(addr);

    INC_R(2);
    INC_T(19);
    INC_PC(3);
}

/* LD (IX/Y+d),n */
static void ld_xy_n(CSimulatorObject* self, void* lookup, int args[]) {
    int xyh = args[0];
    int xyl = args[1];
    unsigned long long* reg = self->registers;
    byte* mem = self->memory;

    unsigned xy = REG(xyl) + 256 * REG(xyh);
    unsigned offset = MEMGET((REG(PC) + 2) % 65536);
    unsigned addr = (xy + (offset < 128 ? offset : offset - 256)) % 65536;
#ifdef CONTENTION
    CONTEND {
        unsigned pc = REG(PC);
        unsigned pc2 = (pc + 2) % 65536;
        unsigned pc3 = (pc + 3) % 65536;
        CPATTERN(14, pc, 4, (pc + 1) % 65536, 4, pc2, 3, pc3, 3, pc3, 1, pc3, 1, addr, 3);
    }
#endif
    if (addr > 0x3FFF) {
        MEMSET(addr, MEMGET((REG(PC) + 3) % 65536));
    }

    INC_R(2);
    INC_T(19);
    INC_PC(4);
}

/* LD (IX/Y+d),r */
static void ld_xy_r(CSimulatorObject* self, void* lookup, int args[]) {
    int xyh = args[0];
    int xyl = args[1];
    int r = args[2];
    unsigned long long* reg = self->registers;
    byte* mem = self->memory;

    unsigned xy = REG(xyl) + 256 * REG(xyh);
    unsigned offset = MEMGET((REG(PC) + 2) % 65536);
    unsigned addr = (xy + (offset < 128 ? offset : offset - 256)) % 65536;
#ifdef CONTENTION
    CONTEND {
        unsigned pc = REG(PC);
        unsigned pc2 = (pc + 2) % 65536;
        CPATTERN(18, pc, 4, (pc + 1) % 65536, 4, pc2, 3, pc2, 1, pc2, 1, pc2, 1, pc2, 1, pc2, 1, addr, 3);
    }
#endif
    if (addr > 0x3FFF) {
        MEMSET(addr, REG(r));
    }

    INC_R(2);
    INC_T(19);
    INC_PC(3);
}

/* LD BC/DE/HL/SP/IX/IY,nn */
static void ld_rr_nn(CSimulatorObject* self, void* lookup, int args[]) {
    int r_inc = args[0];
    int timing = args[1];
    int size = args[2];
    int rh = args[3];
    int rl = args[4];
    unsigned long long* reg = self->registers;
    byte* mem = self->memory;

#ifdef CONTENTION
    CONTEND {
        unsigned pc = REG(PC);
        if (size == 3) {
            CPATTERN(6, pc, 4, (pc + 1) % 65536, 3, (pc + 2) % 65536, 3);
        } else {
            CPATTERN(8, pc, 4, (pc + 1) % 65536, 4, (pc + 2) % 65536, 3, (pc + 3) % 65536, 3);
        }
    }
#endif
    if (rl == SP) {
        REG(SP) = MEMGET((REG(PC) + 1) % 65536) + 256 * MEMGET((REG(PC) + 2) % 65536);
    } else {
        REG(rl) = MEMGET((REG(PC) + size - 2) % 65536);
        REG(rh) = MEMGET((REG(PC) + size - 1) % 65536);
    }

    INC_R(r_inc);
    INC_T(timing);
    INC_PC(size);
}

/* LD A,(nn) */
static void ld_a_m(CSimulatorObject* self, void* lookup, int args[]) {
    unsigned long long* reg = self->registers;
    byte* mem = self->memory;

#ifdef CONTENTION
    CONTEND {
        unsigned pc = REG(PC);
        unsigned pc1 = (pc + 1) % 65536;
        unsigned pc2 = (pc + 2) % 65536;
        CPATTERN(8, pc, 4, pc1, 3, pc2, 3, MEMGET(pc1) + 256 * MEMGET(pc2), 3);
    }
#endif
    REG(A) = MEMGET(MEMGET((REG(PC) + 1) % 65536) + 256 * MEMGET((REG(PC) + 2) % 65536));

    INC_R(1);
    INC_T(13);
    INC_PC(3);
}

/* LD (nn),A */
static void ld_m_a(CSimulatorObject* self, void* lookup, int args[]) {
    unsigned long long* reg = self->registers;
    byte* mem = self->memory;

    unsigned addr = MEMGET((REG(PC) + 1) % 65536) + 256 * MEMGET((REG(PC) + 2) % 65536);
#ifdef CONTENTION
    CONTEND {
        unsigned pc = REG(PC);
        CPATTERN(8, pc, 4, (pc + 1) % 65536, 3, (pc + 2) % 65536, 3, addr, 3);
    }
#endif
    if (addr > 0x3FFF) {
        MEMSET(addr, REG(A));
    }

    INC_R(1);
    INC_T(13);
    INC_PC(3);
}

/* LD BC/DE/HL/SP/IX/IY,(nn) */
static void ld_rr_mm(CSimulatorObject* self, void* lookup, int args[]) {
    int r_inc = args[0];
    int timing = args[1];
    int size = args[2];
    int rh = args[3];
    int rl = args[4];
    unsigned long long* reg = self->registers;
    byte* mem = self->memory;

    unsigned addr = MEMGET((REG(PC) + size - 2) % 65536) + 256 * MEMGET((REG(PC) + size - 1) % 65536);
#ifdef CONTENTION
    CONTEND {
        unsigned pc = REG(PC);
        if (size == 3) {
            CPATTERN(10, pc, 4, (pc + 1) % 65536, 3, (pc + 2) % 65536, 3, addr, 3, (addr + 1) % 65536, 3);
        } else {
            CPATTERN(12, pc, 4, (pc + 1) % 65536, 4, (pc + 2) % 65536, 3, (pc + 3) % 65536, 3, addr, 3, (addr + 1) % 65536, 3);
        }
    }
#endif
    if (rl == SP) {
        REG(SP) = MEMGET(addr) + 256 * MEMGET((addr + 1) % 65536);
    } else {
        REG(rl) = MEMGET(addr);
        REG(rh) = MEMGET((addr + 1) % 65536);
    }

    INC_R(r_inc);
    INC_T(timing);
    INC_PC(size);
}

/* LD (nn),BC/DE/HL/SP/IX/IY */
static void ld_mm_rr(CSimulatorObject* self, void* lookup, int args[]) {
    int r_inc = args[0];
    int timing = args[1];
    int size = args[2];
    int rh = args[3];
    int rl = args[4];
    unsigned long long* reg = self->registers;
    byte* mem = self->memory;

    unsigned addr = MEMGET((REG(PC) + size - 2) % 65536) + 256 * MEMGET((REG(PC) + size - 1) % 65536);
#ifdef CONTENTION
    CONTEND {
        unsigned pc = REG(PC);
        if (size == 3) {
            CPATTERN(10, pc, 4, (pc + 1) % 65536, 3, (pc + 2) % 65536, 3, addr, 3, (addr + 1) % 65536, 3);
        } else {
            CPATTERN(12, pc, 4, (pc + 1) % 65536, 4, (pc + 2) % 65536, 3, (pc + 3) % 65536, 3, addr, 3, (addr + 1) % 65536, 3);
        }
    }
#endif
    if (rl == SP) {
        unsigned sp = REG(SP);
        if (addr > 0x3FFF) {
            MEMSET(addr, sp % 256);
        }
        addr = (addr + 1) % 65536;
        if (addr > 0x3FFF) {
            MEMSET(addr, sp / 256);
        }
    } else {
        if (addr > 0x3FFF) {
            MEMSET(addr, REG(rl));
        }
        addr = (addr + 1) % 65536;
        if (addr > 0x3FFF) {
            MEMSET(addr, REG(rh));
        }
    }

    INC_R(r_inc);
    INC_T(timing);
    INC_PC(size);
}

/* LDI / LDD / LDIR / LDDR */
static void ldi(CSimulatorObject* self, void* lookup, int args[]) {
    int inc = args[0];
    int repeat = args[1];
    unsigned long long* reg = self->registers;
    byte* mem = self->memory;

    unsigned hl = REG(L) + 256 * REG(H);
    unsigned de = REG(E) + 256 * REG(D);
    unsigned bc = REG(C) + 256 * REG(B);
    byte at_hl = MEMGET(hl);
    if (de > 0x3FFF) {
        MEMSET(de, at_hl);
    }
    hl = (hl + inc) % 65536;
    de = (de + inc) % 65536;
    bc = (bc - 1) % 65536;
    REG(L) = hl % 256;
    REG(H) = hl / 256;
    REG(E) = de % 256;
    REG(D) = de / 256;
    REG(C) = bc % 256;
    REG(B) = bc / 256;
    if (repeat && bc) {
        REG(F) = (REG(F) & 0xC1) + ((REG(PC) / 256) & 0x28) + 0x04;
#ifdef CONTENTION
        CONTEND {
            unsigned pc = REG(PC);
            hl = (hl - inc) % 65536;
            de = (de - inc) % 65536;
            CPATTERN(22, pc, 4, (pc + 1) % 65536, 4, hl, 3, de, 3, de, 1, de, 1, de, 1, de, 1, de, 1, de, 1, de, 1);
        }
#endif
        INC_T(21);
    } else {
        unsigned n = REG(A) + at_hl;
        REG(F) = (REG(F) & 0xC1) + (n & 0x02) * 16 + (n & 0x08) + (bc > 0) * 0x04;
#ifdef CONTENTION
        CONTEND {
            unsigned pc = REG(PC);
            hl = (hl - inc) % 65536;
            de = (de - inc) % 65536;
            CPATTERN(12, pc, 4, (pc + 1) % 65536, 4, hl, 3, de, 3, de, 1, de, 1);
        }
#endif
        INC_T(16);
        INC_PC(2);
    }

    INC_R(2);
}

/* LD SP,HL/IX/IY */
static void ld_sp_rr(CSimulatorObject* self, void* lookup, int args[]) {
    int r_inc = args[0];
    int timing = args[1];
    int size = args[2];
    int rh = args[3];
    int rl = args[4];
    unsigned long long* reg = self->registers;

#ifdef CONTENTION
    CONTEND {
        unsigned pc = REG(PC);
        unsigned ir = REG(R) + 256 * REG(I);
        if (size == 1) {
            CPATTERN(6, pc, 4, ir, 1, ir, 1);
        } else {
            CPATTERN(8, pc, 4, (pc + 1) % 65536, 4, ir, 1, ir, 1);
        }
    }
#endif
    REG(SP) = REG(rl) + 256 * REG(rh);

    INC_R(r_inc);
    INC_T(timing);
    INC_PC(size);
}

/* NEG */
static void neg(CSimulatorObject* self, void* lookup, int args[]) {
    unsigned long long* reg = self->registers;

#ifdef CONTENTION
    CONTEND {
        unsigned pc = REG(PC);
        CPATTERN(4, pc, 4, (pc + 1) % 65536, 4);
    }
#endif
    unsigned old_a = REG(A);
    REG(A) = NEG[old_a][0];
    REG(F) = NEG[old_a][1];

    INC_R(2);
    INC_T(8);
    INC_PC(2);
}

/* NOP and equivalents */
static void nop(CSimulatorObject* self, void* lookup, int args[]) {
    int r_inc = args[0];
    int timing = args[1];
    int size = args[2];
    unsigned long long* reg = self->registers;

    INC_R(r_inc);
#ifdef CONTENTION
    CONTEND {
        unsigned pc = REG(PC);
        if (size == 1) {
            CPATTERN(2, pc, 4);
        } else {
            CPATTERN(4, pc, 4, (pc + 1) % 65536, 4);
        }
    }
#endif
    INC_T(timing);
    INC_PC(size);
}

/* OUT (n),A */
static void out_a(CSimulatorObject* self, void* lookup, int args[]) {
    unsigned long long* reg = self->registers;
    byte* mem = self->memory;

    unsigned port = MEMGET((REG(PC) + 1) % 65536) + 256 * REG(A);
#ifdef CONTENTION
    CONTEND {
        unsigned pc = REG(PC);
        CPATTERN(6, pc, 4, (pc + 1) % 65536, 3, port, 0);
    }
#endif
    byte value = REG(A);
    OUT(port, value);
    if (self->out_tracer) {
        PyObject* m_args = Py_BuildValue("(IB)", port, value);
        PyObject* rv = PyObject_Call(self->out_tracer, m_args, NULL);
        Py_XDECREF(m_args);
        if (rv == NULL) {
            return;
        }
        Py_DECREF(rv);
    }

    INC_R(1);
    INC_T(11);
    INC_PC(2);
}

/* OUT (C),r/0 */
static void out_c(CSimulatorObject* self, void* lookup, int args[]) {
    int r = args[0];
    unsigned long long* reg = self->registers;
    byte* mem = self->memory;

    unsigned port = REG(C) + 256 * REG(B);
#ifdef CONTENTION
    CONTEND {
        unsigned pc = REG(PC);
        CPATTERN(6, pc, 4, (pc + 1) % 65536, 4, port, 0);
    }
#endif
    byte value = r >= 0 ? REG(r) : 0;
    OUT(port, value);
    if (self->out_tracer) {
        PyObject* m_args = Py_BuildValue("(IB)", port, value);
        PyObject* rv = PyObject_Call(self->out_tracer, m_args, NULL);
        Py_XDECREF(m_args);
        if (rv == NULL) {
            return;
        }
        Py_DECREF(rv);
    }

    INC_R(2);
    INC_T(12);
    INC_PC(2);
}

/* OUTI / OUTD / OTIR / OTDR */
static void outi(CSimulatorObject* self, void* lookup, int args[]) {
    int inc = args[0];
    int repeat = args[1];
    unsigned long long* reg = self->registers;
    byte* mem = self->memory;

    unsigned hl = REG(L) + 256 * REG(H);
    unsigned b = (REG(B) - 1) % 256;
    unsigned port = REG(C) + 256 * b;
    byte value = MEMGET(hl);
    OUT(port, value);
    if (self->out_tracer) {
        PyObject* m_args = Py_BuildValue("(IB)", port, value);
        PyObject* rv = PyObject_Call(self->out_tracer, m_args, NULL);
        Py_XDECREF(m_args);
        if (rv == NULL) {
            return;
        }
        Py_DECREF(rv);
    }
    hl = (hl + inc) % 65536;
    unsigned l = hl % 256;
    REG(L) = l;
    REG(H) = hl / 256;
    REG(B) = b;
    unsigned j = l + value;
    unsigned n = (value & 0x80) / 64;
    int cf = j > 0xFF ? 1 : 0;
    if (repeat && b) {
        unsigned hf = 0;
        unsigned p = 0;
        if (cf) {
            if (n) {
                hf = (b % 16 == 0) * 0x10;
                p = PARITY[(j % 8) ^ b ^ ((b - 1) % 8)];
            } else {
                hf = ((b & 0x0F) == 0x0F) * 0x10;
                p = PARITY[(j % 8) ^ b ^ ((b + 1) % 8)];
            }
        } else {
            hf = 0;
            p = PARITY[(j % 8) ^ b ^ (b % 8)];
        }
        REG(F) = (b & 0x80) + ((REG(PC) >> 8) & 0x28) + hf + p + n + cf;
#ifdef CONTENTION
        CONTEND {
            unsigned pc = REG(PC);
            unsigned bc = REG(C) + 256 * ((b + 1) % 256);
            unsigned ir = REG(R) + 256 * REG(I);
            hl = (hl - inc) % 65536;
            CPATTERN(20, pc, 4, (pc + 1) % 65536, 4, ir, 1, hl, 3, port, 0, bc, 1, bc, 1, bc, 1, bc, 1, bc, 1);
        }
#endif
        INC_T(21);
    } else {
        REG(F) = (b & 0xA8) + (b == 0) * 0x40 + cf * 0x11 + PARITY[(j % 8) ^ b] + n;
#ifdef CONTENTION
        CONTEND {
            unsigned pc = REG(PC);
            unsigned ir = REG(R) + 256 * REG(I);
            hl = (hl - inc) % 65536;
            CPATTERN(10, pc, 4, (pc + 1) % 65536, 4, ir, 1, hl, 3, port, 0);
        }
#endif
        INC_PC(2);
        INC_T(16);
    }

    INC_R(2);
}

/* POP AF/BC/DE/HL/IX/IY */
static void pop(CSimulatorObject* self, void* lookup, int args[]) {
    int r_inc = args[0];
    int timing = args[1];
    int size = args[2];
    int rh = args[3];
    int rl = args[4];
    unsigned long long* reg = self->registers;
    byte* mem = self->memory;

    unsigned sp = REG(SP);
#ifdef CONTENTION
    CONTEND {
        unsigned pc = REG(PC);
        if (size == 1) {
            CPATTERN(6, pc, 4, sp, 3, (sp + 1) % 65536, 3);
        } else {
            CPATTERN(8, pc, 4, (pc + 1) % 65536, 4, sp, 3, (sp + 1) % 65536, 3);
        }
    }
#endif
    REG(SP) = (sp + 2) % 65536;
    REG(rl) = MEMGET(sp);
    REG(rh) = MEMGET((sp + 1) % 65536);

    INC_R(r_inc);
    INC_T(timing);
    INC_PC(size);
}

/* PUSH AF/BC/DE/HL/IX/IY */
static void push(CSimulatorObject* self, void* lookup, int args[]) {
    int r_inc = args[0];
    int timing = args[1];
    int size = args[2];
    int rh = args[3];
    int rl = args[4];
    unsigned long long* reg = self->registers;
    byte* mem = self->memory;

    unsigned sp = (REG(SP) - 2) % 65536;
    REG(SP) = sp;
    if (sp > 0x3FFF) {
        MEMSET(sp, REG(rl));
    }
    sp = (sp + 1) % 65536;
    if (sp > 0x3FFF) {
        MEMSET(sp, REG(rh));
    }
#ifdef CONTENTION
    CONTEND {
        unsigned pc = REG(PC);
        unsigned ir = REG(R) + 256 * REG(I);
        if (size == 1) {
            CPATTERN(8, pc, 4, ir, 1, sp, 3, (sp - 1) % 65536, 3);
        } else {
            CPATTERN(10, pc, 4, (pc + 1) % 65536, 4, ir, 1, sp, 3, (sp - 1) % 65536, 3);
        }
    }
#endif

    INC_R(r_inc);
    INC_T(timing);
    INC_PC(size);
}

/* RES n,(HL) */
static void res_hl(CSimulatorObject* self, void* lookup, int args[]) {
    int bit = args[0];
    unsigned long long* reg = self->registers;

    unsigned hl = REG(L) + 256 * REG(H);
#ifdef CONTENTION
    CONTEND {
        unsigned pc = REG(PC);
        CPATTERN(10, pc, 4, (pc + 1) % 65536, 4, hl, 3, hl, 1, hl, 3);
    }
#endif
    if (hl > 0x3FFF) {
        byte* mem = self->memory;
        MEMSET(hl, MEMGET(hl) & bit);
    }

    INC_R(2);
    INC_T(15);
    INC_PC(2);
}

/* RES n,r */
static void res_r(CSimulatorObject* self, void* lookup, int args[]) {
    int bit = args[0];
    int r = args[1];
    unsigned long long* reg = self->registers;

#ifdef CONTENTION
    CONTEND {
        unsigned pc = REG(PC);
        CPATTERN(4, pc, 4, (pc + 1) % 65536, 4);
    }
#endif
    REG(r) &= bit;

    INC_R(2);
    INC_T(8);
    INC_PC(2);
}

/* RES n,(IX/Y+d) */
static void res_xy(CSimulatorObject* self, void* lookup, int args[]) {
    int bit = args[0];
    int xyh = args[1];
    int xyl = args[2];
    int dest = args[3];
    unsigned long long* reg = self->registers;
    byte* mem = self->memory;

    unsigned xy = REG(xyl) + 256 * REG(xyh);
    unsigned offset = MEMGET((REG(PC) + 2) % 65536);
    unsigned addr = (xy + (offset < 128 ? offset : offset - 256)) % 65536;
#ifdef CONTENTION
    CONTEND {
        unsigned pc = REG(PC);
        unsigned pc3 = (pc + 3) % 65536;
        CPATTERN(18, pc, 4, (pc + 1) % 65536, 4, (pc + 2) % 65536, 3, pc3, 3, pc3, 1, pc3, 1, addr, 3, addr, 1, addr, 3);
    }
#endif
    byte value = MEMGET(addr) & bit;
    if (addr > 0x3FFF) {
        MEMSET(addr, value);
    }
    if (dest >= 0) {
        REG(dest) = value;
    }

    INC_R(2);
    INC_T(23);
    INC_PC(4);
}

/* RET / RET cc */
static void ret(CSimulatorObject* self, void* lookup, int args[]) {
    unsigned c_and = args[0];
    unsigned c_val = args[1];
    unsigned long long* reg = self->registers;
    byte* mem = self->memory;

    if (c_and) {
        if ((REG(F) & c_and) == c_val) {
#ifdef CONTENTION
            CONTEND {
                unsigned pc = REG(PC);
                unsigned ir = REG(R) + 256 * REG(I);
                CPATTERN(4, pc, 4, ir, 1);
            }
#endif
            INC_T(5);
            INC_PC(1);
        } else {
            unsigned sp = REG(SP);
#ifdef CONTENTION
            CONTEND {
                unsigned pc = REG(PC);
                unsigned ir = REG(R) + 256 * REG(I);
                CPATTERN(8, pc, 4, ir, 1, sp, 3, (sp + 1) % 65536, 3);
            }
#endif
            INC_T(11);
            REG(SP) = (sp + 2) % 65536;
            REG(PC) = MEMGET(sp) + 256 * MEMGET((sp + 1) % 65536);
        }
    } else {
        unsigned sp = REG(SP);
#ifdef CONTENTION
        CONTEND {
            unsigned pc = REG(PC);
            CPATTERN(6, pc, 4, sp, 3, (sp + 1) % 65536, 3);
        }
#endif
        INC_T(10);
        REG(SP) = (sp + 2) % 65536;
        REG(PC) = MEMGET(sp) + 256 * MEMGET((sp + 1) % 65536);
    }

    INC_R(1);
}

/* RETI / RETN */
static void reti(CSimulatorObject* self, void* lookup, int args[]) {
    unsigned long long* reg = self->registers;
    byte* mem = self->memory;

    unsigned sp = REG(SP);
#ifdef CONTENTION
        CONTEND {
            unsigned pc = REG(PC);
            CPATTERN(8, pc, 4, (pc + 1) % 65536, 4, sp, 3, (sp + 1) % 65536, 3);
        }
#endif
    REG(SP) = (sp + 2) % 65536;

    INC_R(2);
    INC_T(14);
    REG(PC) = MEMGET(sp) + 256 * MEMGET((sp + 1) % 65536);
}

/* RLD */
static void rld(CSimulatorObject* self, void* lookup, int args[]) {
    unsigned long long* reg = self->registers;
    byte* mem = self->memory;

    unsigned hl = REG(L) + 256 * REG(H);
#ifdef CONTENTION
    CONTEND {
        unsigned pc = REG(PC);
        CPATTERN(16, pc, 4, (pc + 1) % 65536, 4, hl, 3, hl, 1, hl, 1, hl, 1, hl, 1, hl, 3);
    }
#endif
    unsigned a = REG(A);
    byte at_hl = MEMGET(hl);
    if (hl > 0x3FFF) {
        MEMSET(hl, ((at_hl * 16) % 256) + (a % 16));
    }
    REG(A) = (a & 240) + at_hl / 16;
    REG(F) = SZ53P[REG(A)] + (REG(F) & 1);

    INC_R(2);
    INC_T(18);
    INC_PC(2);
}

/* RRD */
static void rrd(CSimulatorObject* self, void* lookup, int args[]) {
    unsigned long long* reg = self->registers;
    byte* mem = self->memory;

    unsigned hl = REG(L) + 256 * REG(H);
#ifdef CONTENTION
    CONTEND {
        unsigned pc = REG(PC);
        CPATTERN(16, pc, 4, (pc + 1) % 65536, 4, hl, 3, hl, 1, hl, 1, hl, 1, hl, 1, hl, 3);
    }
#endif
    unsigned a = REG(A);
    byte at_hl = MEMGET(hl);
    if (hl > 0x3FFF) {
        MEMSET(hl, ((a * 16) % 256) + (at_hl / 16));
    }
    REG(A) = (a & 240) + (at_hl % 16);
    REG(F) = SZ53P[REG(A)] + (REG(F) & 1);

    INC_R(2);
    INC_T(18);
    INC_PC(2);
}

/* RST n */
static void rst(CSimulatorObject* self, void* lookup, int args[]) {
    int addr = args[0];
    unsigned long long* reg = self->registers;
    byte* mem = self->memory;

    unsigned ret_addr = (REG(PC) + 1) % 65536;
    unsigned sp = (REG(SP) - 2) % 65536;
    REG(SP) = sp;
    if (sp > 0x3FFF) {
        MEMSET(sp, ret_addr % 256);
    }
    sp = (sp + 1) % 65536;
    if (sp > 0x3FFF) {
        MEMSET(sp, ret_addr / 256);
    }
#ifdef CONTENTION
    CONTEND {
        unsigned ir = REG(R) + 256 * REG(I);
        CPATTERN(8, REG(PC), 4, ir, 1, sp, 3, (sp - 1) % 65536, 3);
    }
#endif

    INC_R(1);
    INC_T(11);
    REG(PC) = addr;
}

/* SBC HL,BC/DE/HL/SP */
static void sbc_hl(CSimulatorObject* self, void* lookup, int args[]) {
    unsigned rh = args[0];
    unsigned rl = args[1];
    unsigned long long* reg = self->registers;

#ifdef CONTENTION
    CONTEND {
        unsigned pc = REG(PC);
        unsigned ir = REG(R) + 256 * REG(I);
        CPATTERN(18, pc, 4, (pc + 1) % 65536, 4, ir, 1, ir, 1, ir, 1, ir, 1, ir, 1, ir, 1, ir, 1);
    }
#endif
    unsigned rr = REG(rl) + 256 * REG(rh);
    unsigned hl = REG(L) + 256 * REG(H);
    unsigned rr_c = rr + (REG(F) & 1);
    unsigned result = (hl - rr_c) % 65536;
    unsigned f = 0;

    if (hl < rr_c) {
        f = 0x03; // ......NC
    } else {
        f = 0x02; // ......N.
    }
    if (result == 0) {
        f += 0x40; // .Z......
    }
    if (hl % 4096 < rr_c % 4096) {
        f += 0x10; // ...H....
    }
    if ((hl ^ rr) > 0x7FFF && (hl ^ result) > 0x7FFF) {
        // Minuend and subtrahend signs are different - overflow if the
        // minuend's sign differs from the sign of the result
        f += 0x04; // .....P..
    }

    unsigned h = result / 256;
    REG(F) = f + (h & 0xA8);
    REG(L) = result % 256;
    REG(H) = h;

    INC_R(2);
    INC_T(15);
    INC_PC(2);
}

/* SET n,(HL) */
static void set_hl(CSimulatorObject* self, void* lookup, int args[]) {
    int bit = args[0];
    unsigned long long* reg = self->registers;

    unsigned hl = REG(L) + 256 * REG(H);
#ifdef CONTENTION
    CONTEND {
        unsigned pc = REG(PC);
        CPATTERN(10, pc, 4, (pc + 1) % 65536, 4, hl, 3, hl, 1, hl, 3);
    }
#endif
    if (hl > 0x3FFF) {
        byte* mem = self->memory;
        MEMSET(hl, MEMGET(hl) | bit);
    }

    INC_R(2);
    INC_T(15);
    INC_PC(2);
}

/* SET n,r */
static void set_r(CSimulatorObject* self, void* lookup, int args[]) {
    int bit = args[0];
    int r = args[1];
    unsigned long long* reg = self->registers;

#ifdef CONTENTION
    CONTEND {
        unsigned pc = REG(PC);
        CPATTERN(4, pc, 4, (pc + 1) % 65536, 4);
    }
#endif
    REG(r) |= bit;

    INC_R(2);
    INC_T(8);
    INC_PC(2);
}

/* SET n,(IX/Y+d) */
static void set_xy(CSimulatorObject* self, void* lookup, int args[]) {
    int bit = args[0];
    int xyh = args[1];
    int xyl = args[2];
    int dest = args[3];
    unsigned long long* reg = self->registers;
    byte* mem = self->memory;

    unsigned xy = REG(xyl) + 256 * REG(xyh);
    unsigned offset = MEMGET((REG(PC) + 2) % 65536);
    unsigned addr = (xy + (offset < 128 ? offset : offset - 256)) % 65536;
#ifdef CONTENTION
    CONTEND {
        unsigned pc = REG(PC);
        unsigned pc3 = (pc + 3) % 65536;
        CPATTERN(18, pc, 4, (pc + 1) % 65536, 4, (pc + 2) % 65536, 3, pc3, 3, pc3, 1, pc3, 1, addr, 3, addr, 1, addr, 3);
    }
#endif
    byte value = MEMGET(addr) | bit;
    if (addr > 0x3FFF) {
        MEMSET(addr, value);
    }
    if (dest >= 0) {
        REG(dest) = value;
    }

    INC_R(2);
    INC_T(23);
    INC_PC(4);
}

/*****************************************************************************/

static OpcodeFunction opcodes[256] = {
    {nop, NULL, {1, 4, 1}},                         // 00 NOP
    {ld_rr_nn, NULL, {1, 10, 3, 2, 3}},             // 01 LD BC,nn
    {ld_rr_r, NULL, {2, 3, 0}},                     // 02 LD (BC),A
    {inc_dec_rr, NULL, {1, 6, 1, 1, 2, 3}},         // 03 INC BC
    {fc_r, INC, {1, 4, 1, 2}},                      // 04 INC B
    {fc_r, DEC, {1, 4, 1, 2}},                      // 05 DEC B
    {ld_r_n, NULL, {1, 7, 2, 2}},                   // 06 LD B,n
    {af_r, RLCA, {1, 4, 1, 1}},                     // 07 RLCA
    {ex_af, NULL, {0}},                             // 08 EX AF,AF'
    {add_rr, NULL, {1, 11, 1, 6, 7, 2, 3}},         // 09 ADD HL,BC
    {ld_r_rr, NULL, {0, 2, 3}},                     // 0A LD A,(BC)
    {inc_dec_rr, NULL, {1, 6, 1, -1, 2, 3}},        // 0B DEC BC
    {fc_r, INC, {1, 4, 1, 3}},                      // 0C INC C
    {fc_r, DEC, {1, 4, 1, 3}},                      // 0D DEC C
    {ld_r_n, NULL, {1, 7, 2, 3}},                   // 0E LD C,n
    {af_r, RRCA, {1, 4, 1, 1}},                     // 0F RRCA
    {djnz, NULL, {0}},                              // 10 DJNZ nn
    {ld_rr_nn, NULL, {1, 10, 3, 4, 5}},             // 11 LD DE,nn
    {ld_rr_r, NULL, {4, 5, 0}},                     // 12 LD (DE),A
    {inc_dec_rr, NULL, {1, 6, 1, 1, 4, 5}},         // 13 INC DE
    {fc_r, INC, {1, 4, 1, 4}},                      // 14 INC D
    {fc_r, DEC, {1, 4, 1, 4}},                      // 15 DEC D
    {ld_r_n, NULL, {1, 7, 2, 4}},                   // 16 LD D,n
    {af_r, RLA, {1, 4, 1, 1}},                      // 17 RLA
    {jr, NULL, {0, 0}},                             // 18 JR nn
    {add_rr, NULL, {1, 11, 1, 6, 7, 4, 5}},         // 19 ADD HL,DE
    {ld_r_rr, NULL, {0, 4, 5}},                     // 1A LD A,(DE)
    {inc_dec_rr, NULL, {1, 6, 1, -1, 4, 5}},        // 1B DEC DE
    {fc_r, INC, {1, 4, 1, 5}},                      // 1C INC E
    {fc_r, DEC, {1, 4, 1, 5}},                      // 1D DEC E
    {ld_r_n, NULL, {1, 7, 2, 5}},                   // 1E LD E,n
    {af_r, RRA, {1, 4, 1, 1}},                      // 1F RRA
    {jr, NULL, {64, 0}},                            // 20 JR NZ,nn
    {ld_rr_nn, NULL, {1, 10, 3, 6, 7}},             // 21 LD HL,nn
    {ld_mm_rr, NULL, {1, 16, 3, 6, 7}},             // 22 LD (nn),HL
    {inc_dec_rr, NULL, {1, 6, 1, 1, 6, 7}},         // 23 INC HL
    {fc_r, INC, {1, 4, 1, 6}},                      // 24 INC H
    {fc_r, DEC, {1, 4, 1, 6}},                      // 25 DEC H
    {ld_r_n, NULL, {1, 7, 2, 6}},                   // 26 LD H,n
    {af_r, DAA, {1, 4, 1, 1}},                      // 27 DAA
    {jr, NULL, {64, 64}},                           // 28 JR Z,nn
    {add_rr, NULL, {1, 11, 1, 6, 7, 6, 7}},         // 29 ADD HL,HL
    {ld_rr_mm, NULL, {1, 16, 3, 6, 7}},             // 2A LD HL,(nn)
    {inc_dec_rr, NULL, {1, 6, 1, -1, 6, 7}},        // 2B DEC HL
    {fc_r, INC, {1, 4, 1, 7}},                      // 2C INC L
    {fc_r, DEC, {1, 4, 1, 7}},                      // 2D DEC L
    {ld_r_n, NULL, {1, 7, 2, 7}},                   // 2E LD L,n
    {af_r, CPL, {1, 4, 1, 1}},                      // 2F CPL
    {jr, NULL, {1, 0}},                             // 30 JR NC,nn
    {ld_rr_nn, NULL, {1, 10, 3, 13, 12}},           // 31 LD SP,nn
    {ld_m_a, NULL, {0}},                            // 32 LD (nn),A
    {inc_dec_rr, NULL, {1, 6, 1, 1, 13, 12}},       // 33 INC SP
    {fc_hl, INC, {1, 11, 1}},                       // 34 INC (HL)
    {fc_hl, DEC, {1, 11, 1}},                       // 35 DEC (HL)
    {ld_hl_n, NULL, {0}},                           // 36 LD (HL),n
    {cf, SCF, {0}},                                 // 37 SCF
    {jr, NULL, {1, 1}},                             // 38 JR C,nn
    {add_rr, NULL, {1, 11, 1, 6, 7, 13, 12}},       // 39 ADD HL,SP
    {ld_a_m, NULL, {0}},                            // 3A LD A,(nn)
    {inc_dec_rr, NULL, {1, 6, 1, -1, 13, 12}},      // 3B DEC SP
    {fc_r, INC, {1, 4, 1, 0}},                      // 3C INC A
    {fc_r, DEC, {1, 4, 1, 0}},                      // 3D DEC A
    {ld_r_n, NULL, {1, 7, 2, 0}},                   // 3E LD A,n
    {cf, CCF, {0}},                                 // 3F CCF
    {nop, NULL, {1, 4, 1}},                         // 40 LD B,B
    {ld_r_r, NULL, {1, 4, 1, 2, 3}},                // 41 LD B,C
    {ld_r_r, NULL, {1, 4, 1, 2, 4}},                // 42 LD B,D
    {ld_r_r, NULL, {1, 4, 1, 2, 5}},                // 43 LD B,E
    {ld_r_r, NULL, {1, 4, 1, 2, 6}},                // 44 LD B,H
    {ld_r_r, NULL, {1, 4, 1, 2, 7}},                // 45 LD B,L
    {ld_r_rr, NULL, {2, 6, 7}},                     // 46 LD B,(HL)
    {ld_r_r, NULL, {1, 4, 1, 2, 0}},                // 47 LD B,A
    {ld_r_r, NULL, {1, 4, 1, 3, 2}},                // 48 LD C,B
    {nop, NULL, {1, 4, 1}},                         // 49 LD C,C
    {ld_r_r, NULL, {1, 4, 1, 3, 4}},                // 4A LD C,D
    {ld_r_r, NULL, {1, 4, 1, 3, 5}},                // 4B LD C,E
    {ld_r_r, NULL, {1, 4, 1, 3, 6}},                // 4C LD C,H
    {ld_r_r, NULL, {1, 4, 1, 3, 7}},                // 4D LD C,L
    {ld_r_rr, NULL, {3, 6, 7}},                     // 4E LD C,(HL)
    {ld_r_r, NULL, {1, 4, 1, 3, 0}},                // 4F LD C,A
    {ld_r_r, NULL, {1, 4, 1, 4, 2}},                // 50 LD D,B
    {ld_r_r, NULL, {1, 4, 1, 4, 3}},                // 51 LD D,C
    {nop, NULL, {1, 4, 1}},                         // 52 LD D,D
    {ld_r_r, NULL, {1, 4, 1, 4, 5}},                // 53 LD D,E
    {ld_r_r, NULL, {1, 4, 1, 4, 6}},                // 54 LD D,H
    {ld_r_r, NULL, {1, 4, 1, 4, 7}},                // 55 LD D,L
    {ld_r_rr, NULL, {4, 6, 7}},                     // 56 LD D,(HL)
    {ld_r_r, NULL, {1, 4, 1, 4, 0}},                // 57 LD D,A
    {ld_r_r, NULL, {1, 4, 1, 5, 2}},                // 58 LD E,B
    {ld_r_r, NULL, {1, 4, 1, 5, 3}},                // 59 LD E,C
    {ld_r_r, NULL, {1, 4, 1, 5, 4}},                // 5A LD E,D
    {nop, NULL, {1, 4, 1}},                         // 5B LD E,E
    {ld_r_r, NULL, {1, 4, 1, 5, 6}},                // 5C LD E,H
    {ld_r_r, NULL, {1, 4, 1, 5, 7}},                // 5D LD E,L
    {ld_r_rr, NULL, {5, 6, 7}},                     // 5E LD E,(HL)
    {ld_r_r, NULL, {1, 4, 1, 5, 0}},                // 5F LD E,A
    {ld_r_r, NULL, {1, 4, 1, 6, 2}},                // 60 LD H,B
    {ld_r_r, NULL, {1, 4, 1, 6, 3}},                // 61 LD H,C
    {ld_r_r, NULL, {1, 4, 1, 6, 4}},                // 62 LD H,D
    {ld_r_r, NULL, {1, 4, 1, 6, 5}},                // 63 LD H,E
    {nop, NULL, {1, 4, 1}},                         // 64 LD H,H
    {ld_r_r, NULL, {1, 4, 1, 6, 7}},                // 65 LD H,L
    {ld_r_rr, NULL, {6, 6, 7}},                     // 66 LD H,(HL)
    {ld_r_r, NULL, {1, 4, 1, 6, 0}},                // 67 LD H,A
    {ld_r_r, NULL, {1, 4, 1, 7, 2}},                // 68 LD L,B
    {ld_r_r, NULL, {1, 4, 1, 7, 3}},                // 69 LD L,C
    {ld_r_r, NULL, {1, 4, 1, 7, 4}},                // 6A LD L,D
    {ld_r_r, NULL, {1, 4, 1, 7, 5}},                // 6B LD L,E
    {ld_r_r, NULL, {1, 4, 1, 7, 6}},                // 6C LD L,H
    {nop, NULL, {1, 4, 1}},                         // 6D LD L,L
    {ld_r_rr, NULL, {7, 6, 7}},                     // 6E LD L,(HL)
    {ld_r_r, NULL, {1, 4, 1, 7, 0}},                // 6F LD L,A
    {ld_rr_r, NULL, {6, 7, 2}},                     // 70 LD (HL),B
    {ld_rr_r, NULL, {6, 7, 3}},                     // 71 LD (HL),C
    {ld_rr_r, NULL, {6, 7, 4}},                     // 72 LD (HL),D
    {ld_rr_r, NULL, {6, 7, 5}},                     // 73 LD (HL),E
    {ld_rr_r, NULL, {6, 7, 6}},                     // 74 LD (HL),H
    {ld_rr_r, NULL, {6, 7, 7}},                     // 75 LD (HL),L
    {halt, NULL, {0}},                              // 76 HALT
    {ld_rr_r, NULL, {6, 7, 0}},                     // 77 LD (HL),A
    {ld_r_r, NULL, {1, 4, 1, 0, 2}},                // 78 LD A,B
    {ld_r_r, NULL, {1, 4, 1, 0, 3}},                // 79 LD A,C
    {ld_r_r, NULL, {1, 4, 1, 0, 4}},                // 7A LD A,D
    {ld_r_r, NULL, {1, 4, 1, 0, 5}},                // 7B LD A,E
    {ld_r_r, NULL, {1, 4, 1, 0, 6}},                // 7C LD A,H
    {ld_r_r, NULL, {1, 4, 1, 0, 7}},                // 7D LD A,L
    {ld_r_rr, NULL, {0, 6, 7}},                     // 7E LD A,(HL)
    {nop, NULL, {1, 4, 1}},                         // 7F LD A,A
    {af_r, ADD, {1, 4, 1, 2}},                      // 80 ADD A,B
    {af_r, ADD, {1, 4, 1, 3}},                      // 81 ADD A,C
    {af_r, ADD, {1, 4, 1, 4}},                      // 82 ADD A,D
    {af_r, ADD, {1, 4, 1, 5}},                      // 83 ADD A,E
    {af_r, ADD, {1, 4, 1, 6}},                      // 84 ADD A,H
    {af_r, ADD, {1, 4, 1, 7}},                      // 85 ADD A,L
    {af_hl, ADD, {0}},                              // 86 ADD A,(HL)
    {af_r, ADD, {1, 4, 1, 0}},                      // 87 ADD A,A
    {afc_r, ADC, {1, 4, 1, 2}},                     // 88 ADC A,B
    {afc_r, ADC, {1, 4, 1, 3}},                     // 89 ADC A,C
    {afc_r, ADC, {1, 4, 1, 4}},                     // 8A ADC A,D
    {afc_r, ADC, {1, 4, 1, 5}},                     // 8B ADC A,E
    {afc_r, ADC, {1, 4, 1, 6}},                     // 8C ADC A,H
    {afc_r, ADC, {1, 4, 1, 7}},                     // 8D ADC A,L
    {afc_hl, ADC, {0}},                             // 8E ADC A,(HL)
    {fc_r, ADC_A_A, {1, 4, 1, 0}},                  // 8F ADC A,A
    {af_r, SUB, {1, 4, 1, 2}},                      // 90 SUB B
    {af_r, SUB, {1, 4, 1, 3}},                      // 91 SUB C
    {af_r, SUB, {1, 4, 1, 4}},                      // 92 SUB D
    {af_r, SUB, {1, 4, 1, 5}},                      // 93 SUB E
    {af_r, SUB, {1, 4, 1, 6}},                      // 94 SUB H
    {af_r, SUB, {1, 4, 1, 7}},                      // 95 SUB L
    {af_hl, SUB, {0}},                              // 96 SUB (HL)
    {af_r, SUB, {1, 4, 1, 0}},                      // 97 SUB A
    {afc_r, SBC, {1, 4, 1, 2}},                     // 98 SBC A,B
    {afc_r, SBC, {1, 4, 1, 3}},                     // 99 SBC A,C
    {afc_r, SBC, {1, 4, 1, 4}},                     // 9A SBC A,D
    {afc_r, SBC, {1, 4, 1, 5}},                     // 9B SBC A,E
    {afc_r, SBC, {1, 4, 1, 6}},                     // 9C SBC A,H
    {afc_r, SBC, {1, 4, 1, 7}},                     // 9D SBC A,L
    {afc_hl, SBC, {0}},                             // 9E SBC A,(HL)
    {fc_r, SBC_A_A, {1, 4, 1, 0}},                  // 9F SBC A,A
    {af_r, AND, {1, 4, 1, 2}},                      // A0 AND B
    {af_r, AND, {1, 4, 1, 3}},                      // A1 AND C
    {af_r, AND, {1, 4, 1, 4}},                      // A2 AND D
    {af_r, AND, {1, 4, 1, 5}},                      // A3 AND E
    {af_r, AND, {1, 4, 1, 6}},                      // A4 AND H
    {af_r, AND, {1, 4, 1, 7}},                      // A5 AND L
    {af_hl, AND, {0}},                              // A6 AND (HL)
    {af_r, AND, {1, 4, 1, 0}},                      // A7 AND A
    {af_r, XOR, {1, 4, 1, 2}},                      // A8 XOR B
    {af_r, XOR, {1, 4, 1, 3}},                      // A9 XOR C
    {af_r, XOR, {1, 4, 1, 4}},                      // AA XOR D
    {af_r, XOR, {1, 4, 1, 5}},                      // AB XOR E
    {af_r, XOR, {1, 4, 1, 6}},                      // AC XOR H
    {af_r, XOR, {1, 4, 1, 7}},                      // AD XOR L
    {af_hl, XOR, {0}},                              // AE XOR (HL)
    {af_r, XOR, {1, 4, 1, 0}},                      // AF XOR A
    {af_r, OR, {1, 4, 1, 2}},                       // B0 OR B
    {af_r, OR, {1, 4, 1, 3}},                       // B1 OR C
    {af_r, OR, {1, 4, 1, 4}},                       // B2 OR D
    {af_r, OR, {1, 4, 1, 5}},                       // B3 OR E
    {af_r, OR, {1, 4, 1, 6}},                       // B4 OR H
    {af_r, OR, {1, 4, 1, 7}},                       // B5 OR L
    {af_hl, OR, {0}},                               // B6 OR (HL)
    {af_r, OR, {1, 4, 1, 0}},                       // B7 OR A
    {af_r, CP, {1, 4, 1, 2}},                       // B8 CP B
    {af_r, CP, {1, 4, 1, 3}},                       // B9 CP C
    {af_r, CP, {1, 4, 1, 4}},                       // BA CP D
    {af_r, CP, {1, 4, 1, 5}},                       // BB CP E
    {af_r, CP, {1, 4, 1, 6}},                       // BC CP H
    {af_r, CP, {1, 4, 1, 7}},                       // BD CP L
    {af_hl, CP, {0}},                               // BE CP (HL)
    {af_r, CP, {1, 4, 1, 0}},                       // BF CP A
    {ret, NULL, {64, 64}},                          // C0 RET NZ
    {pop, NULL, {1, 10, 1, 2, 3}},                  // C1 POP BC
    {jp, NULL, {64, 0}},                            // C2 JP NZ,nn
    {jp, NULL, {0, 0}},                             // C3 JP nn
    {call, NULL, {64, 64}},                         // C4 CALL NZ,nn
    {push, NULL, {1, 11, 1, 2, 3}},                 // C5 PUSH BC
    {af_n, ADD, {0}},                               // C6 ADD A,n
    {rst, NULL, {0}},                               // C7 RST $00
    {ret, NULL, {64, 0}},                           // C8 RET Z
    {ret, NULL, {0, 0}},                            // C9 RET
    {jp, NULL, {64, 64}},                           // CA JP Z,nn
    {NULL, NULL, {0}},                              // CB prefix
    {call, NULL, {64, 0}},                          // CC CALL Z,nn
    {call, NULL, {0, 0}},                           // CD CALL nn
    {afc_n, ADC, {0}},                              // CE ADC A,n
    {rst, NULL, {8}},                               // CF RST $08
    {ret, NULL, {1, 1}},                            // D0 RET NC
    {pop, NULL, {1, 10, 1, 4, 5}},                  // D1 POP DE
    {jp, NULL, {1, 0}},                             // D2 JP NC,nn
    {out_a, NULL, {0}},                             // D3 OUT (n),A
    {call, NULL, {1, 1}},                           // D4 CALL NC,nn
    {push, NULL, {1, 11, 1, 4, 5}},                 // D5 PUSH DE
    {af_n, SUB, {0}},                               // D6 SUB n
    {rst, NULL, {16}},                              // D7 RST $10
    {ret, NULL, {1, 0}},                            // D8 RET C
    {exx, NULL, {0}},                               // D9 EXX
    {jp, NULL, {1, 1}},                             // DA JP C,nn
    {in_a, NULL, {0}},                              // DB IN A,(n)
    {call, NULL, {1, 0}},                           // DC CALL C,nn
    {NULL, NULL, {0}},                              // DD prefix
    {afc_n, SBC, {0}},                              // DE SBC A,n
    {rst, NULL, {24}},                              // DF RST $18
    {ret, NULL, {4, 4}},                            // E0 RET PO
    {pop, NULL, {1, 10, 1, 6, 7}},                  // E1 POP HL
    {jp, NULL, {4, 0}},                             // E2 JP PO,nn
    {ex_sp, NULL, {1, 19, 1, 6, 7}},                // E3 EX (SP),HL
    {call, NULL, {4, 4}},                           // E4 CALL PO,nn
    {push, NULL, {1, 11, 1, 6, 7}},                 // E5 PUSH HL
    {af_n, AND, {0}},                               // E6 AND n
    {rst, NULL, {32}},                              // E7 RST $20
    {ret, NULL, {4, 0}},                            // E8 RET PE
    {jp_rr, NULL, {1, 4, 6, 7}},                    // E9 JP (HL)
    {jp, NULL, {4, 4}},                             // EA JP PE,nn
    {ex_de_hl, NULL, {0}},                          // EB EX DE,HL
    {call, NULL, {4, 0}},                           // EC CALL PE,nn
    {NULL, NULL, {0}},                              // ED prefix
    {af_n, XOR, {0}},                               // EE XOR n
    {rst, NULL, {40}},                              // EF RST $28
    {ret, NULL, {128, 128}},                        // F0 RET P
    {pop, NULL, {1, 10, 1, 0, 1}},                  // F1 POP AF
    {jp, NULL, {128, 0}},                           // F2 JP P,nn
    {di_ei, NULL, {0}},                             // F3 DI
    {call, NULL, {128, 128}},                       // F4 CALL P,nn
    {push, NULL, {1, 11, 1, 0, 1}},                 // F5 PUSH AF
    {af_n, OR, {0}},                                // F6 OR n
    {rst, NULL, {48}},                              // F7 RST $30
    {ret, NULL, {128, 0}},                          // F8 RET M
    {ld_sp_rr, NULL, {1, 6, 1, 6, 7}},              // F9 LD SP,HL
    {jp, NULL, {128, 128}},                         // FA JP M,nn
    {di_ei, NULL, {1}},                             // FB EI
    {call, NULL, {128, 0}},                         // FC CALL M,nn
    {NULL, NULL, {0}},                              // FD prefix
    {af_n, CP, {0}},                                // FE CP n
    {rst, NULL, {56}},                              // FF RST $38
};

static OpcodeFunction after_CB[256] = {
    {f_r, RLC, {2}},                                // CB00 RLC B
    {f_r, RLC, {3}},                                // CB01 RLC C
    {f_r, RLC, {4}},                                // CB02 RLC D
    {f_r, RLC, {5}},                                // CB03 RLC E
    {f_r, RLC, {6}},                                // CB04 RLC H
    {f_r, RLC, {7}},                                // CB05 RLC L
    {f_hl, RLC, {0}},                               // CB06 RLC (HL)
    {f_r, RLC, {0}},                                // CB07 RLC A
    {f_r, RRC, {2}},                                // CB08 RRC B
    {f_r, RRC, {3}},                                // CB09 RRC C
    {f_r, RRC, {4}},                                // CB0A RRC D
    {f_r, RRC, {5}},                                // CB0B RRC E
    {f_r, RRC, {6}},                                // CB0C RRC H
    {f_r, RRC, {7}},                                // CB0D RRC L
    {f_hl, RRC, {0}},                               // CB0E RRC (HL)
    {f_r, RRC, {0}},                                // CB0F RRC A
    {fc_r, RL, {2, 8, 2, 2}},                       // CB10 RL B
    {fc_r, RL, {2, 8, 2, 3}},                       // CB11 RL C
    {fc_r, RL, {2, 8, 2, 4}},                       // CB12 RL D
    {fc_r, RL, {2, 8, 2, 5}},                       // CB13 RL E
    {fc_r, RL, {2, 8, 2, 6}},                       // CB14 RL H
    {fc_r, RL, {2, 8, 2, 7}},                       // CB15 RL L
    {fc_hl, RL, {2, 15, 2}},                        // CB16 RL (HL)
    {fc_r, RL, {2, 8, 2, 0}},                       // CB17 RL A
    {fc_r, RR, {2, 8, 2, 2}},                       // CB18 RR B
    {fc_r, RR, {2, 8, 2, 3}},                       // CB19 RR C
    {fc_r, RR, {2, 8, 2, 4}},                       // CB1A RR D
    {fc_r, RR, {2, 8, 2, 5}},                       // CB1B RR E
    {fc_r, RR, {2, 8, 2, 6}},                       // CB1C RR H
    {fc_r, RR, {2, 8, 2, 7}},                       // CB1D RR L
    {fc_hl, RR, {2, 15, 2}},                        // CB1E RR (HL)
    {fc_r, RR, {2, 8, 2, 0}},                       // CB1F RR A
    {f_r, SLA, {2}},                                // CB20 SLA B
    {f_r, SLA, {3}},                                // CB21 SLA C
    {f_r, SLA, {4}},                                // CB22 SLA D
    {f_r, SLA, {5}},                                // CB23 SLA E
    {f_r, SLA, {6}},                                // CB24 SLA H
    {f_r, SLA, {7}},                                // CB25 SLA L
    {f_hl, SLA, {0}},                               // CB26 SLA (HL)
    {f_r, SLA, {0}},                                // CB27 SLA A
    {f_r, SRA, {2}},                                // CB28 SRA B
    {f_r, SRA, {3}},                                // CB29 SRA C
    {f_r, SRA, {4}},                                // CB2A SRA D
    {f_r, SRA, {5}},                                // CB2B SRA E
    {f_r, SRA, {6}},                                // CB2C SRA H
    {f_r, SRA, {7}},                                // CB2D SRA L
    {f_hl, SRA, {0}},                               // CB2E SRA (HL)
    {f_r, SRA, {0}},                                // CB2F SRA A
    {f_r, SLL, {2}},                                // CB30 SLL B
    {f_r, SLL, {3}},                                // CB31 SLL C
    {f_r, SLL, {4}},                                // CB32 SLL D
    {f_r, SLL, {5}},                                // CB33 SLL E
    {f_r, SLL, {6}},                                // CB34 SLL H
    {f_r, SLL, {7}},                                // CB35 SLL L
    {f_hl, SLL, {0}},                               // CB36 SLL (HL)
    {f_r, SLL, {0}},                                // CB37 SLL A
    {f_r, SRL, {2}},                                // CB38 SRL B
    {f_r, SRL, {3}},                                // CB39 SRL C
    {f_r, SRL, {4}},                                // CB3A SRL D
    {f_r, SRL, {5}},                                // CB3B SRL E
    {f_r, SRL, {6}},                                // CB3C SRL H
    {f_r, SRL, {7}},                                // CB3D SRL L
    {f_hl, SRL, {0}},                               // CB3E SRL (HL)
    {f_r, SRL, {0}},                                // CB3F SRL A
    {bit_r, NULL, {0, 2}},                          // CB40 BIT 0,B
    {bit_r, NULL, {0, 3}},                          // CB41 BIT 0,C
    {bit_r, NULL, {0, 4}},                          // CB42 BIT 0,D
    {bit_r, NULL, {0, 5}},                          // CB43 BIT 0,E
    {bit_r, NULL, {0, 6}},                          // CB44 BIT 0,H
    {bit_r, NULL, {0, 7}},                          // CB45 BIT 0,L
    {bit_hl, NULL, {0}},                            // CB46 BIT 0,(HL)
    {bit_r, NULL, {0, 0}},                          // CB47 BIT 0,A
    {bit_r, NULL, {1, 2}},                          // CB48 BIT 1,B
    {bit_r, NULL, {1, 3}},                          // CB49 BIT 1,C
    {bit_r, NULL, {1, 4}},                          // CB4A BIT 1,D
    {bit_r, NULL, {1, 5}},                          // CB4B BIT 1,E
    {bit_r, NULL, {1, 6}},                          // CB4C BIT 1,H
    {bit_r, NULL, {1, 7}},                          // CB4D BIT 1,L
    {bit_hl, NULL, {1}},                            // CB4E BIT 1,(HL)
    {bit_r, NULL, {1, 0}},                          // CB4F BIT 1,A
    {bit_r, NULL, {2, 2}},                          // CB50 BIT 2,B
    {bit_r, NULL, {2, 3}},                          // CB51 BIT 2,C
    {bit_r, NULL, {2, 4}},                          // CB52 BIT 2,D
    {bit_r, NULL, {2, 5}},                          // CB53 BIT 2,E
    {bit_r, NULL, {2, 6}},                          // CB54 BIT 2,H
    {bit_r, NULL, {2, 7}},                          // CB55 BIT 2,L
    {bit_hl, NULL, {2}},                            // CB56 BIT 2,(HL)
    {bit_r, NULL, {2, 0}},                          // CB57 BIT 2,A
    {bit_r, NULL, {3, 2}},                          // CB58 BIT 3,B
    {bit_r, NULL, {3, 3}},                          // CB59 BIT 3,C
    {bit_r, NULL, {3, 4}},                          // CB5A BIT 3,D
    {bit_r, NULL, {3, 5}},                          // CB5B BIT 3,E
    {bit_r, NULL, {3, 6}},                          // CB5C BIT 3,H
    {bit_r, NULL, {3, 7}},                          // CB5D BIT 3,L
    {bit_hl, NULL, {3}},                            // CB5E BIT 3,(HL)
    {bit_r, NULL, {3, 0}},                          // CB5F BIT 3,A
    {bit_r, NULL, {4, 2}},                          // CB60 BIT 4,B
    {bit_r, NULL, {4, 3}},                          // CB61 BIT 4,C
    {bit_r, NULL, {4, 4}},                          // CB62 BIT 4,D
    {bit_r, NULL, {4, 5}},                          // CB63 BIT 4,E
    {bit_r, NULL, {4, 6}},                          // CB64 BIT 4,H
    {bit_r, NULL, {4, 7}},                          // CB65 BIT 4,L
    {bit_hl, NULL, {4}},                            // CB66 BIT 4,(HL)
    {bit_r, NULL, {4, 0}},                          // CB67 BIT 4,A
    {bit_r, NULL, {5, 2}},                          // CB68 BIT 5,B
    {bit_r, NULL, {5, 3}},                          // CB69 BIT 5,C
    {bit_r, NULL, {5, 4}},                          // CB6A BIT 5,D
    {bit_r, NULL, {5, 5}},                          // CB6B BIT 5,E
    {bit_r, NULL, {5, 6}},                          // CB6C BIT 5,H
    {bit_r, NULL, {5, 7}},                          // CB6D BIT 5,L
    {bit_hl, NULL, {5}},                            // CB6E BIT 5,(HL)
    {bit_r, NULL, {5, 0}},                          // CB6F BIT 5,A
    {bit_r, NULL, {6, 2}},                          // CB70 BIT 6,B
    {bit_r, NULL, {6, 3}},                          // CB71 BIT 6,C
    {bit_r, NULL, {6, 4}},                          // CB72 BIT 6,D
    {bit_r, NULL, {6, 5}},                          // CB73 BIT 6,E
    {bit_r, NULL, {6, 6}},                          // CB74 BIT 6,H
    {bit_r, NULL, {6, 7}},                          // CB75 BIT 6,L
    {bit_hl, NULL, {6}},                            // CB76 BIT 6,(HL)
    {bit_r, NULL, {6, 0}},                          // CB77 BIT 6,A
    {bit_r, NULL, {7, 2}},                          // CB78 BIT 7,B
    {bit_r, NULL, {7, 3}},                          // CB79 BIT 7,C
    {bit_r, NULL, {7, 4}},                          // CB7A BIT 7,D
    {bit_r, NULL, {7, 5}},                          // CB7B BIT 7,E
    {bit_r, NULL, {7, 6}},                          // CB7C BIT 7,H
    {bit_r, NULL, {7, 7}},                          // CB7D BIT 7,L
    {bit_hl, NULL, {7}},                            // CB7E BIT 7,(HL)
    {bit_r, NULL, {7, 0}},                          // CB7F BIT 7,A
    {res_r, NULL, {254, 2}},                        // CB80 RES 0,B
    {res_r, NULL, {254, 3}},                        // CB81 RES 0,C
    {res_r, NULL, {254, 4}},                        // CB82 RES 0,D
    {res_r, NULL, {254, 5}},                        // CB83 RES 0,E
    {res_r, NULL, {254, 6}},                        // CB84 RES 0,H
    {res_r, NULL, {254, 7}},                        // CB85 RES 0,L
    {res_hl, NULL, {254}},                          // CB86 RES 0,(HL)
    {res_r, NULL, {254, 0}},                        // CB87 RES 0,A
    {res_r, NULL, {253, 2}},                        // CB88 RES 1,B
    {res_r, NULL, {253, 3}},                        // CB89 RES 1,C
    {res_r, NULL, {253, 4}},                        // CB8A RES 1,D
    {res_r, NULL, {253, 5}},                        // CB8B RES 1,E
    {res_r, NULL, {253, 6}},                        // CB8C RES 1,H
    {res_r, NULL, {253, 7}},                        // CB8D RES 1,L
    {res_hl, NULL, {253}},                          // CB8E RES 1,(HL)
    {res_r, NULL, {253, 0}},                        // CB8F RES 1,A
    {res_r, NULL, {251, 2}},                        // CB90 RES 2,B
    {res_r, NULL, {251, 3}},                        // CB91 RES 2,C
    {res_r, NULL, {251, 4}},                        // CB92 RES 2,D
    {res_r, NULL, {251, 5}},                        // CB93 RES 2,E
    {res_r, NULL, {251, 6}},                        // CB94 RES 2,H
    {res_r, NULL, {251, 7}},                        // CB95 RES 2,L
    {res_hl, NULL, {251}},                          // CB96 RES 2,(HL)
    {res_r, NULL, {251, 0}},                        // CB97 RES 2,A
    {res_r, NULL, {247, 2}},                        // CB98 RES 3,B
    {res_r, NULL, {247, 3}},                        // CB99 RES 3,C
    {res_r, NULL, {247, 4}},                        // CB9A RES 3,D
    {res_r, NULL, {247, 5}},                        // CB9B RES 3,E
    {res_r, NULL, {247, 6}},                        // CB9C RES 3,H
    {res_r, NULL, {247, 7}},                        // CB9D RES 3,L
    {res_hl, NULL, {247}},                          // CB9E RES 3,(HL)
    {res_r, NULL, {247, 0}},                        // CB9F RES 3,A
    {res_r, NULL, {239, 2}},                        // CBA0 RES 4,B
    {res_r, NULL, {239, 3}},                        // CBA1 RES 4,C
    {res_r, NULL, {239, 4}},                        // CBA2 RES 4,D
    {res_r, NULL, {239, 5}},                        // CBA3 RES 4,E
    {res_r, NULL, {239, 6}},                        // CBA4 RES 4,H
    {res_r, NULL, {239, 7}},                        // CBA5 RES 4,L
    {res_hl, NULL, {239}},                          // CBA6 RES 4,(HL)
    {res_r, NULL, {239, 0}},                        // CBA7 RES 4,A
    {res_r, NULL, {223, 2}},                        // CBA8 RES 5,B
    {res_r, NULL, {223, 3}},                        // CBA9 RES 5,C
    {res_r, NULL, {223, 4}},                        // CBAA RES 5,D
    {res_r, NULL, {223, 5}},                        // CBAB RES 5,E
    {res_r, NULL, {223, 6}},                        // CBAC RES 5,H
    {res_r, NULL, {223, 7}},                        // CBAD RES 5,L
    {res_hl, NULL, {223}},                          // CBAE RES 5,(HL)
    {res_r, NULL, {223, 0}},                        // CBAF RES 5,A
    {res_r, NULL, {191, 2}},                        // CBB0 RES 6,B
    {res_r, NULL, {191, 3}},                        // CBB1 RES 6,C
    {res_r, NULL, {191, 4}},                        // CBB2 RES 6,D
    {res_r, NULL, {191, 5}},                        // CBB3 RES 6,E
    {res_r, NULL, {191, 6}},                        // CBB4 RES 6,H
    {res_r, NULL, {191, 7}},                        // CBB5 RES 6,L
    {res_hl, NULL, {191}},                          // CBB6 RES 6,(HL)
    {res_r, NULL, {191, 0}},                        // CBB7 RES 6,A
    {res_r, NULL, {127, 2}},                        // CBB8 RES 7,B
    {res_r, NULL, {127, 3}},                        // CBB9 RES 7,C
    {res_r, NULL, {127, 4}},                        // CBBA RES 7,D
    {res_r, NULL, {127, 5}},                        // CBBB RES 7,E
    {res_r, NULL, {127, 6}},                        // CBBC RES 7,H
    {res_r, NULL, {127, 7}},                        // CBBD RES 7,L
    {res_hl, NULL, {127}},                          // CBBE RES 7,(HL)
    {res_r, NULL, {127, 0}},                        // CBBF RES 7,A
    {set_r, NULL, {1, 2}},                          // CBC0 SET 0,B
    {set_r, NULL, {1, 3}},                          // CBC1 SET 0,C
    {set_r, NULL, {1, 4}},                          // CBC2 SET 0,D
    {set_r, NULL, {1, 5}},                          // CBC3 SET 0,E
    {set_r, NULL, {1, 6}},                          // CBC4 SET 0,H
    {set_r, NULL, {1, 7}},                          // CBC5 SET 0,L
    {set_hl, NULL, {1}},                            // CBC6 SET 0,(HL)
    {set_r, NULL, {1, 0}},                          // CBC7 SET 0,A
    {set_r, NULL, {2, 2}},                          // CBC8 SET 1,B
    {set_r, NULL, {2, 3}},                          // CBC9 SET 1,C
    {set_r, NULL, {2, 4}},                          // CBCA SET 1,D
    {set_r, NULL, {2, 5}},                          // CBCB SET 1,E
    {set_r, NULL, {2, 6}},                          // CBCC SET 1,H
    {set_r, NULL, {2, 7}},                          // CBCD SET 1,L
    {set_hl, NULL, {2}},                            // CBCE SET 1,(HL)
    {set_r, NULL, {2, 0}},                          // CBCF SET 1,A
    {set_r, NULL, {4, 2}},                          // CBD0 SET 2,B
    {set_r, NULL, {4, 3}},                          // CBD1 SET 2,C
    {set_r, NULL, {4, 4}},                          // CBD2 SET 2,D
    {set_r, NULL, {4, 5}},                          // CBD3 SET 2,E
    {set_r, NULL, {4, 6}},                          // CBD4 SET 2,H
    {set_r, NULL, {4, 7}},                          // CBD5 SET 2,L
    {set_hl, NULL, {4}},                            // CBD6 SET 2,(HL)
    {set_r, NULL, {4, 0}},                          // CBD7 SET 2,A
    {set_r, NULL, {8, 2}},                          // CBD8 SET 3,B
    {set_r, NULL, {8, 3}},                          // CBD9 SET 3,C
    {set_r, NULL, {8, 4}},                          // CBDA SET 3,D
    {set_r, NULL, {8, 5}},                          // CBDB SET 3,E
    {set_r, NULL, {8, 6}},                          // CBDC SET 3,H
    {set_r, NULL, {8, 7}},                          // CBDD SET 3,L
    {set_hl, NULL, {8}},                            // CBDE SET 3,(HL)
    {set_r, NULL, {8, 0}},                          // CBDF SET 3,A
    {set_r, NULL, {16, 2}},                         // CBE0 SET 4,B
    {set_r, NULL, {16, 3}},                         // CBE1 SET 4,C
    {set_r, NULL, {16, 4}},                         // CBE2 SET 4,D
    {set_r, NULL, {16, 5}},                         // CBE3 SET 4,E
    {set_r, NULL, {16, 6}},                         // CBE4 SET 4,H
    {set_r, NULL, {16, 7}},                         // CBE5 SET 4,L
    {set_hl, NULL, {16}},                           // CBE6 SET 4,(HL)
    {set_r, NULL, {16, 0}},                         // CBE7 SET 4,A
    {set_r, NULL, {32, 2}},                         // CBE8 SET 5,B
    {set_r, NULL, {32, 3}},                         // CBE9 SET 5,C
    {set_r, NULL, {32, 4}},                         // CBEA SET 5,D
    {set_r, NULL, {32, 5}},                         // CBEB SET 5,E
    {set_r, NULL, {32, 6}},                         // CBEC SET 5,H
    {set_r, NULL, {32, 7}},                         // CBED SET 5,L
    {set_hl, NULL, {32}},                           // CBEE SET 5,(HL)
    {set_r, NULL, {32, 0}},                         // CBEF SET 5,A
    {set_r, NULL, {64, 2}},                         // CBF0 SET 6,B
    {set_r, NULL, {64, 3}},                         // CBF1 SET 6,C
    {set_r, NULL, {64, 4}},                         // CBF2 SET 6,D
    {set_r, NULL, {64, 5}},                         // CBF3 SET 6,E
    {set_r, NULL, {64, 6}},                         // CBF4 SET 6,H
    {set_r, NULL, {64, 7}},                         // CBF5 SET 6,L
    {set_hl, NULL, {64}},                           // CBF6 SET 6,(HL)
    {set_r, NULL, {64, 0}},                         // CBF7 SET 6,A
    {set_r, NULL, {128, 2}},                        // CBF8 SET 7,B
    {set_r, NULL, {128, 3}},                        // CBF9 SET 7,C
    {set_r, NULL, {128, 4}},                        // CBFA SET 7,D
    {set_r, NULL, {128, 5}},                        // CBFB SET 7,E
    {set_r, NULL, {128, 6}},                        // CBFC SET 7,H
    {set_r, NULL, {128, 7}},                        // CBFD SET 7,L
    {set_hl, NULL, {128}},                          // CBFE SET 7,(HL)
    {set_r, NULL, {128, 0}},                        // CBFF SET 7,A
};

static OpcodeFunction after_ED[256] = {
    {nop, NULL, {2, 8, 2}},                         // ED00
    {nop, NULL, {2, 8, 2}},                         // ED01
    {nop, NULL, {2, 8, 2}},                         // ED02
    {nop, NULL, {2, 8, 2}},                         // ED03
    {nop, NULL, {2, 8, 2}},                         // ED04
    {nop, NULL, {2, 8, 2}},                         // ED05
    {nop, NULL, {2, 8, 2}},                         // ED06
    {nop, NULL, {2, 8, 2}},                         // ED07
    {nop, NULL, {2, 8, 2}},                         // ED08
    {nop, NULL, {2, 8, 2}},                         // ED09
    {nop, NULL, {2, 8, 2}},                         // ED0A
    {nop, NULL, {2, 8, 2}},                         // ED0B
    {nop, NULL, {2, 8, 2}},                         // ED0C
    {nop, NULL, {2, 8, 2}},                         // ED0D
    {nop, NULL, {2, 8, 2}},                         // ED0E
    {nop, NULL, {2, 8, 2}},                         // ED0F
    {nop, NULL, {2, 8, 2}},                         // ED10
    {nop, NULL, {2, 8, 2}},                         // ED11
    {nop, NULL, {2, 8, 2}},                         // ED12
    {nop, NULL, {2, 8, 2}},                         // ED13
    {nop, NULL, {2, 8, 2}},                         // ED14
    {nop, NULL, {2, 8, 2}},                         // ED15
    {nop, NULL, {2, 8, 2}},                         // ED16
    {nop, NULL, {2, 8, 2}},                         // ED17
    {nop, NULL, {2, 8, 2}},                         // ED18
    {nop, NULL, {2, 8, 2}},                         // ED19
    {nop, NULL, {2, 8, 2}},                         // ED1A
    {nop, NULL, {2, 8, 2}},                         // ED1B
    {nop, NULL, {2, 8, 2}},                         // ED1C
    {nop, NULL, {2, 8, 2}},                         // ED1D
    {nop, NULL, {2, 8, 2}},                         // ED1E
    {nop, NULL, {2, 8, 2}},                         // ED1F
    {nop, NULL, {2, 8, 2}},                         // ED20
    {nop, NULL, {2, 8, 2}},                         // ED21
    {nop, NULL, {2, 8, 2}},                         // ED22
    {nop, NULL, {2, 8, 2}},                         // ED23
    {nop, NULL, {2, 8, 2}},                         // ED24
    {nop, NULL, {2, 8, 2}},                         // ED25
    {nop, NULL, {2, 8, 2}},                         // ED26
    {nop, NULL, {2, 8, 2}},                         // ED27
    {nop, NULL, {2, 8, 2}},                         // ED28
    {nop, NULL, {2, 8, 2}},                         // ED29
    {nop, NULL, {2, 8, 2}},                         // ED2A
    {nop, NULL, {2, 8, 2}},                         // ED2B
    {nop, NULL, {2, 8, 2}},                         // ED2C
    {nop, NULL, {2, 8, 2}},                         // ED2D
    {nop, NULL, {2, 8, 2}},                         // ED2E
    {nop, NULL, {2, 8, 2}},                         // ED2F
    {nop, NULL, {2, 8, 2}},                         // ED30
    {nop, NULL, {2, 8, 2}},                         // ED31
    {nop, NULL, {2, 8, 2}},                         // ED32
    {nop, NULL, {2, 8, 2}},                         // ED33
    {nop, NULL, {2, 8, 2}},                         // ED34
    {nop, NULL, {2, 8, 2}},                         // ED35
    {nop, NULL, {2, 8, 2}},                         // ED36
    {nop, NULL, {2, 8, 2}},                         // ED37
    {nop, NULL, {2, 8, 2}},                         // ED38
    {nop, NULL, {2, 8, 2}},                         // ED39
    {nop, NULL, {2, 8, 2}},                         // ED3A
    {nop, NULL, {2, 8, 2}},                         // ED3B
    {nop, NULL, {2, 8, 2}},                         // ED3C
    {nop, NULL, {2, 8, 2}},                         // ED3D
    {nop, NULL, {2, 8, 2}},                         // ED3E
    {nop, NULL, {2, 8, 2}},                         // ED3F
    {in_c, NULL, {2}},                              // ED40 IN B,(C)
    {out_c, NULL, {2}},                             // ED41 OUT (C),B
    {sbc_hl, NULL, {2, 3}},                         // ED42 SBC HL,BC
    {ld_mm_rr, NULL, {2, 20, 4, 2, 3}},             // ED43 LD (nn),BC
    {neg, NULL, {0}},                               // ED44 NEG
    {reti, NULL, {0}},                              // ED45 RETN
    {im, NULL, {0}},                                // ED46 IM 0
    {ld_r_r, NULL, {2, 9, 2, 14, 0}},               // ED47 LD I,A
    {in_c, NULL, {3}},                              // ED48 IN C,(C)
    {out_c, NULL, {3}},                             // ED49 OUT (C),C
    {adc_hl, NULL, {2, 3}},                         // ED4A ADC HL,BC
    {ld_rr_mm, NULL, {2, 20, 4, 2, 3}},             // ED4B LD BC,(nn)
    {neg, NULL, {0}},                               // ED4C NEG
    {reti, NULL, {0}},                              // ED4D RETI
    {im, NULL, {0}},                                // ED4E IM 0
    {ld_r_r, NULL, {2, 9, 2, 15, 0}},               // ED4F LD R,A
    {in_c, NULL, {4}},                              // ED50 IN D,(C)
    {out_c, NULL, {4}},                             // ED51 OUT (C),D
    {sbc_hl, NULL, {4, 5}},                         // ED52 SBC HL,DE
    {ld_mm_rr, NULL, {2, 20, 4, 4, 5}},             // ED53 LD (nn),DE
    {neg, NULL, {0}},                               // ED54 NEG
    {reti, NULL, {0}},                              // ED55 RETN
    {im, NULL, {1}},                                // ED56 IM 1
    {ld_a_ir, NULL, {14}},                          // ED57 LD A,I
    {in_c, NULL, {5}},                              // ED58 IN E,(C)
    {out_c, NULL, {5}},                             // ED59 OUT (C),E
    {adc_hl, NULL, {4, 5}},                         // ED5A ADC HL,DE
    {ld_rr_mm, NULL, {2, 20, 4, 4, 5}},             // ED5B LD DE,(nn)
    {neg, NULL, {0}},                               // ED5C NEG
    {reti, NULL, {0}},                              // ED5D RETN
    {im, NULL, {2}},                                // ED5E IM 2
    {ld_a_ir, NULL, {15}},                          // ED5F LD A,R
    {in_c, NULL, {6}},                              // ED60 IN H,(C)
    {out_c, NULL, {6}},                             // ED61 OUT (C),H
    {sbc_hl, NULL, {6, 7}},                         // ED62 SBC HL,HL
    {ld_mm_rr, NULL, {2, 20, 4, 6, 7}},             // ED63 LD (nn),HL
    {neg, NULL, {0}},                               // ED64 NEG
    {reti, NULL, {0}},                              // ED65 RETN
    {im, NULL, {0}},                                // ED66 IM 0
    {rrd, NULL, {0}},                               // ED67 RRD
    {in_c, NULL, {7}},                              // ED68 IN L,(C)
    {out_c, NULL, {7}},                             // ED69 OUT (C),L
    {adc_hl, NULL, {6, 7}},                         // ED6A ADC HL,HL
    {ld_rr_mm, NULL, {2, 20, 4, 6, 7}},             // ED6B LD HL,(nn)
    {neg, NULL, {0}},                               // ED6C NEG
    {reti, NULL, {0}},                              // ED6D RETN
    {im, NULL, {0}},                                // ED6E IM 0
    {rld, NULL, {0}},                               // ED6F RLD
    {in_c, NULL, {1}},                              // ED70 IN F,(C)
    {out_c, NULL, {-1}},                            // ED71 OUT (C),0
    {sbc_hl, NULL, {13, 12}},                       // ED72 SBC HL,SP
    {ld_mm_rr, NULL, {2, 20, 4, 13, 12}},           // ED73 LD (nn),SP
    {neg, NULL, {0}},                               // ED74 NEG
    {reti, NULL, {0}},                              // ED75 RETN
    {im, NULL, {1}},                                // ED76 IM 1
    {nop, NULL, {2, 8, 2}},                         // ED77
    {in_c, NULL, {0}},                              // ED78 IN A,(C)
    {out_c, NULL, {0}},                             // ED79 OUT (C),A
    {adc_hl, NULL, {13, 12}},                       // ED7A ADC HL,SP
    {ld_rr_mm, NULL, {2, 20, 4, 13, 12}},           // ED7B LD SP,(nn)
    {neg, NULL, {0}},                               // ED7C NEG
    {reti, NULL, {0}},                              // ED7D RETN
    {im, NULL, {2}},                                // ED7E IM 2
    {nop, NULL, {2, 8, 2}},                         // ED7F
    {nop, NULL, {2, 8, 2}},                         // ED80
    {nop, NULL, {2, 8, 2}},                         // ED81
    {nop, NULL, {2, 8, 2}},                         // ED82
    {nop, NULL, {2, 8, 2}},                         // ED83
    {nop, NULL, {2, 8, 2}},                         // ED84
    {nop, NULL, {2, 8, 2}},                         // ED85
    {nop, NULL, {2, 8, 2}},                         // ED86
    {nop, NULL, {2, 8, 2}},                         // ED87
    {nop, NULL, {2, 8, 2}},                         // ED88
    {nop, NULL, {2, 8, 2}},                         // ED89
    {nop, NULL, {2, 8, 2}},                         // ED8A
    {nop, NULL, {2, 8, 2}},                         // ED8B
    {nop, NULL, {2, 8, 2}},                         // ED8C
    {nop, NULL, {2, 8, 2}},                         // ED8D
    {nop, NULL, {2, 8, 2}},                         // ED8E
    {nop, NULL, {2, 8, 2}},                         // ED8F
    {nop, NULL, {2, 8, 2}},                         // ED90
    {nop, NULL, {2, 8, 2}},                         // ED91
    {nop, NULL, {2, 8, 2}},                         // ED92
    {nop, NULL, {2, 8, 2}},                         // ED93
    {nop, NULL, {2, 8, 2}},                         // ED94
    {nop, NULL, {2, 8, 2}},                         // ED95
    {nop, NULL, {2, 8, 2}},                         // ED96
    {nop, NULL, {2, 8, 2}},                         // ED97
    {nop, NULL, {2, 8, 2}},                         // ED98
    {nop, NULL, {2, 8, 2}},                         // ED99
    {nop, NULL, {2, 8, 2}},                         // ED9A
    {nop, NULL, {2, 8, 2}},                         // ED9B
    {nop, NULL, {2, 8, 2}},                         // ED9C
    {nop, NULL, {2, 8, 2}},                         // ED9D
    {nop, NULL, {2, 8, 2}},                         // ED9E
    {nop, NULL, {2, 8, 2}},                         // ED9F
    {ldi, NULL, {1, 0}},                            // EDA0 LDI
    {cpi, NULL, {1, 0}},                            // EDA1 CPI
    {ini, NULL, {1, 0}},                            // EDA2 INI
    {outi, NULL, {1, 0}},                           // EDA3 OUTI
    {nop, NULL, {2, 8, 2}},                         // EDA4
    {nop, NULL, {2, 8, 2}},                         // EDA5
    {nop, NULL, {2, 8, 2}},                         // EDA6
    {nop, NULL, {2, 8, 2}},                         // EDA7
    {ldi, NULL, {-1, 0}},                           // EDA8 LDD
    {cpi, NULL, {-1, 0}},                           // EDA9 CPD
    {ini, NULL, {-1, 0}},                           // EDAA IND
    {outi, NULL, {-1, 0}},                          // EDAB OUTD
    {nop, NULL, {2, 8, 2}},                         // EDAC
    {nop, NULL, {2, 8, 2}},                         // EDAD
    {nop, NULL, {2, 8, 2}},                         // EDAE
    {nop, NULL, {2, 8, 2}},                         // EDAF
    {ldi, NULL, {1, 1}},                            // EDB0 LDIR
    {cpi, NULL, {1, 1}},                            // EDB1 CPIR
    {ini, NULL, {1, 1}},                            // EDB2 INIR
    {outi, NULL, {1, 1}},                           // EDB3 OTIR
    {nop, NULL, {2, 8, 2}},                         // EDB4
    {nop, NULL, {2, 8, 2}},                         // EDB5
    {nop, NULL, {2, 8, 2}},                         // EDB6
    {nop, NULL, {2, 8, 2}},                         // EDB7
    {ldi, NULL, {-1, 1}},                           // EDB8 LDDR
    {cpi, NULL, {-1, 1}},                           // EDB9 CPDR
    {ini, NULL, {-1, 1}},                           // EDBA INDR
    {outi, NULL, {-1, 1}},                          // EDBB OTDR
    {nop, NULL, {2, 8, 2}},                         // EDBC
    {nop, NULL, {2, 8, 2}},                         // EDBD
    {nop, NULL, {2, 8, 2}},                         // EDBE
    {nop, NULL, {2, 8, 2}},                         // EDBF
    {nop, NULL, {2, 8, 2}},                         // EDC0
    {nop, NULL, {2, 8, 2}},                         // EDC1
    {nop, NULL, {2, 8, 2}},                         // EDC2
    {nop, NULL, {2, 8, 2}},                         // EDC3
    {nop, NULL, {2, 8, 2}},                         // EDC4
    {nop, NULL, {2, 8, 2}},                         // EDC5
    {nop, NULL, {2, 8, 2}},                         // EDC6
    {nop, NULL, {2, 8, 2}},                         // EDC7
    {nop, NULL, {2, 8, 2}},                         // EDC8
    {nop, NULL, {2, 8, 2}},                         // EDC9
    {nop, NULL, {2, 8, 2}},                         // EDCA
    {nop, NULL, {2, 8, 2}},                         // EDCB
    {nop, NULL, {2, 8, 2}},                         // EDCC
    {nop, NULL, {2, 8, 2}},                         // EDCD
    {nop, NULL, {2, 8, 2}},                         // EDCE
    {nop, NULL, {2, 8, 2}},                         // EDCF
    {nop, NULL, {2, 8, 2}},                         // EDD0
    {nop, NULL, {2, 8, 2}},                         // EDD1
    {nop, NULL, {2, 8, 2}},                         // EDD2
    {nop, NULL, {2, 8, 2}},                         // EDD3
    {nop, NULL, {2, 8, 2}},                         // EDD4
    {nop, NULL, {2, 8, 2}},                         // EDD5
    {nop, NULL, {2, 8, 2}},                         // EDD6
    {nop, NULL, {2, 8, 2}},                         // EDD7
    {nop, NULL, {2, 8, 2}},                         // EDD8
    {nop, NULL, {2, 8, 2}},                         // EDD9
    {nop, NULL, {2, 8, 2}},                         // EDDA
    {nop, NULL, {2, 8, 2}},                         // EDDB
    {nop, NULL, {2, 8, 2}},                         // EDDC
    {nop, NULL, {2, 8, 2}},                         // EDDD
    {nop, NULL, {2, 8, 2}},                         // EDDE
    {nop, NULL, {2, 8, 2}},                         // EDDF
    {nop, NULL, {2, 8, 2}},                         // EDE0
    {nop, NULL, {2, 8, 2}},                         // EDE1
    {nop, NULL, {2, 8, 2}},                         // EDE2
    {nop, NULL, {2, 8, 2}},                         // EDE3
    {nop, NULL, {2, 8, 2}},                         // EDE4
    {nop, NULL, {2, 8, 2}},                         // EDE5
    {nop, NULL, {2, 8, 2}},                         // EDE6
    {nop, NULL, {2, 8, 2}},                         // EDE7
    {nop, NULL, {2, 8, 2}},                         // EDE8
    {nop, NULL, {2, 8, 2}},                         // EDE9
    {nop, NULL, {2, 8, 2}},                         // EDEA
    {nop, NULL, {2, 8, 2}},                         // EDEB
    {nop, NULL, {2, 8, 2}},                         // EDEC
    {nop, NULL, {2, 8, 2}},                         // EDED
    {nop, NULL, {2, 8, 2}},                         // EDEE
    {nop, NULL, {2, 8, 2}},                         // EDEF
    {nop, NULL, {2, 8, 2}},                         // EDF0
    {nop, NULL, {2, 8, 2}},                         // EDF1
    {nop, NULL, {2, 8, 2}},                         // EDF2
    {nop, NULL, {2, 8, 2}},                         // EDF3
    {nop, NULL, {2, 8, 2}},                         // EDF4
    {nop, NULL, {2, 8, 2}},                         // EDF5
    {nop, NULL, {2, 8, 2}},                         // EDF6
    {nop, NULL, {2, 8, 2}},                         // EDF7
    {nop, NULL, {2, 8, 2}},                         // EDF8
    {nop, NULL, {2, 8, 2}},                         // EDF9
    {nop, NULL, {2, 8, 2}},                         // EDFA
    {nop, NULL, {2, 8, 2}},                         // EDFB
    {nop, NULL, {2, 8, 2}},                         // EDFC
    {nop, NULL, {2, 8, 2}},                         // EDFD
    {nop, NULL, {2, 8, 2}},                         // EDFE
    {nop, NULL, {2, 8, 2}},                         // EDFF
};

static OpcodeFunction after_DD[256] = {
    {nop, NULL, {1, 4, 1}},                         // DD00
    {nop, NULL, {1, 4, 1}},                         // DD01
    {nop, NULL, {1, 4, 1}},                         // DD02
    {nop, NULL, {1, 4, 1}},                         // DD03
    {nop, NULL, {1, 4, 1}},                         // DD04
    {nop, NULL, {1, 4, 1}},                         // DD05
    {nop, NULL, {1, 4, 1}},                         // DD06
    {nop, NULL, {1, 4, 1}},                         // DD07
    {nop, NULL, {1, 4, 1}},                         // DD08
    {add_rr, NULL, {2, 15, 2, 8, 9, 2, 3}},         // DD09 ADD IX,BC
    {nop, NULL, {1, 4, 1}},                         // DD0A
    {nop, NULL, {1, 4, 1}},                         // DD0B
    {nop, NULL, {1, 4, 1}},                         // DD0C
    {nop, NULL, {1, 4, 1}},                         // DD0D
    {nop, NULL, {1, 4, 1}},                         // DD0E
    {nop, NULL, {1, 4, 1}},                         // DD0F
    {nop, NULL, {1, 4, 1}},                         // DD10
    {nop, NULL, {1, 4, 1}},                         // DD11
    {nop, NULL, {1, 4, 1}},                         // DD12
    {nop, NULL, {1, 4, 1}},                         // DD13
    {nop, NULL, {1, 4, 1}},                         // DD14
    {nop, NULL, {1, 4, 1}},                         // DD15
    {nop, NULL, {1, 4, 1}},                         // DD16
    {nop, NULL, {1, 4, 1}},                         // DD17
    {nop, NULL, {1, 4, 1}},                         // DD18
    {add_rr, NULL, {2, 15, 2, 8, 9, 4, 5}},         // DD19 ADD IX,DE
    {nop, NULL, {1, 4, 1}},                         // DD1A
    {nop, NULL, {1, 4, 1}},                         // DD1B
    {nop, NULL, {1, 4, 1}},                         // DD1C
    {nop, NULL, {1, 4, 1}},                         // DD1D
    {nop, NULL, {1, 4, 1}},                         // DD1E
    {nop, NULL, {1, 4, 1}},                         // DD1F
    {nop, NULL, {1, 4, 1}},                         // DD20
    {ld_rr_nn, NULL, {2, 14, 4, 8, 9}},             // DD21 LD IX,nn
    {ld_mm_rr, NULL, {2, 20, 4, 8, 9}},             // DD22 LD (nn),IX
    {inc_dec_rr, NULL, {2, 10, 2, 1, 8, 9}},        // DD23 INC IX
    {fc_r, INC, {2, 8, 2, 8}},                      // DD24 INC IXh
    {fc_r, DEC, {2, 8, 2, 8}},                      // DD25 DEC IXh
    {ld_r_n, NULL, {2, 11, 3, 8}},                  // DD26 LD IXh,n
    {nop, NULL, {1, 4, 1}},                         // DD27
    {nop, NULL, {1, 4, 1}},                         // DD28
    {add_rr, NULL, {2, 15, 2, 8, 9, 8, 9}},         // DD29 ADD IX,IX
    {ld_rr_mm, NULL, {2, 20, 4, 8, 9}},             // DD2A LD IX,(nn)
    {inc_dec_rr, NULL, {2, 10, 2, -1, 8, 9}},       // DD2B DEC IX
    {fc_r, INC, {2, 8, 2, 9}},                      // DD2C INC IXl
    {fc_r, DEC, {2, 8, 2, 9}},                      // DD2D DEC IXl
    {ld_r_n, NULL, {2, 11, 3, 9}},                  // DD2E LD IXl,n
    {nop, NULL, {1, 4, 1}},                         // DD2F
    {nop, NULL, {1, 4, 1}},                         // DD30
    {nop, NULL, {1, 4, 1}},                         // DD31
    {nop, NULL, {1, 4, 1}},                         // DD32
    {nop, NULL, {1, 4, 1}},                         // DD33
    {fc_xy, INC, {3, 8, 9, -1}},                    // DD34 INC (IX+d)
    {fc_xy, DEC, {3, 8, 9, -1}},                    // DD35 DEC (IX+d)
    {ld_xy_n, NULL, {8, 9}},                        // DD36 LD (IX+d),n
    {nop, NULL, {1, 4, 1}},                         // DD37
    {nop, NULL, {1, 4, 1}},                         // DD38
    {add_rr, NULL, {2, 15, 2, 8, 9, 13, 12}},       // DD39 ADD IX,SP
    {nop, NULL, {1, 4, 1}},                         // DD3A
    {nop, NULL, {1, 4, 1}},                         // DD3B
    {nop, NULL, {1, 4, 1}},                         // DD3C
    {nop, NULL, {1, 4, 1}},                         // DD3D
    {nop, NULL, {1, 4, 1}},                         // DD3E
    {nop, NULL, {1, 4, 1}},                         // DD3F
    {nop, NULL, {1, 4, 1}},                         // DD40
    {nop, NULL, {1, 4, 1}},                         // DD41
    {nop, NULL, {1, 4, 1}},                         // DD42
    {nop, NULL, {1, 4, 1}},                         // DD43
    {ld_r_r, NULL, {2, 8, 2, 2, 8}},                // DD44 LD B,IXh
    {ld_r_r, NULL, {2, 8, 2, 2, 9}},                // DD45 LD B,IXl
    {ld_r_xy, NULL, {2, 8, 9}},                     // DD46 LD B,(IX+d)
    {nop, NULL, {1, 4, 1}},                         // DD47
    {nop, NULL, {1, 4, 1}},                         // DD48
    {nop, NULL, {1, 4, 1}},                         // DD49
    {nop, NULL, {1, 4, 1}},                         // DD4A
    {nop, NULL, {1, 4, 1}},                         // DD4B
    {ld_r_r, NULL, {2, 8, 2, 3, 8}},                // DD4C LD C,IXh
    {ld_r_r, NULL, {2, 8, 2, 3, 9}},                // DD4D LD C,IXl
    {ld_r_xy, NULL, {3, 8, 9}},                     // DD4E LD C,(IX+d)
    {nop, NULL, {1, 4, 1}},                         // DD4F
    {nop, NULL, {1, 4, 1}},                         // DD50
    {nop, NULL, {1, 4, 1}},                         // DD51
    {nop, NULL, {1, 4, 1}},                         // DD52
    {nop, NULL, {1, 4, 1}},                         // DD53
    {ld_r_r, NULL, {2, 8, 2, 4, 8}},                // DD54 LD D,IXh
    {ld_r_r, NULL, {2, 8, 2, 4, 9}},                // DD55 LD D,IXl
    {ld_r_xy, NULL, {4, 8, 9}},                     // DD56 LD D,(IX+d)
    {nop, NULL, {1, 4, 1}},                         // DD57
    {nop, NULL, {1, 4, 1}},                         // DD58
    {nop, NULL, {1, 4, 1}},                         // DD59
    {nop, NULL, {1, 4, 1}},                         // DD5A
    {nop, NULL, {1, 4, 1}},                         // DD5B
    {ld_r_r, NULL, {2, 8, 2, 5, 8}},                // DD5C LD E,IXh
    {ld_r_r, NULL, {2, 8, 2, 5, 9}},                // DD5D LD E,IXl
    {ld_r_xy, NULL, {5, 8, 9}},                     // DD5E LD E,(IX+d)
    {nop, NULL, {1, 4, 1}},                         // DD5F
    {ld_r_r, NULL, {2, 8, 2, 8, 2}},                // DD60 LD IXh,B
    {ld_r_r, NULL, {2, 8, 2, 8, 3}},                // DD61 LD IXh,C
    {ld_r_r, NULL, {2, 8, 2, 8, 4}},                // DD62 LD IXh,D
    {ld_r_r, NULL, {2, 8, 2, 8, 5}},                // DD63 LD IXh,E
    {nop, NULL, {2, 8, 2}},                         // DD64 LD IXh,IXh
    {ld_r_r, NULL, {2, 8, 2, 8, 9}},                // DD65 LD IXh,IXl
    {ld_r_xy, NULL, {6, 8, 9}},                     // DD66 LD H,(IX+d)
    {ld_r_r, NULL, {2, 8, 2, 8, 0}},                // DD67 LD IXh,A
    {ld_r_r, NULL, {2, 8, 2, 9, 2}},                // DD68 LD IXl,B
    {ld_r_r, NULL, {2, 8, 2, 9, 3}},                // DD69 LD IXl,C
    {ld_r_r, NULL, {2, 8, 2, 9, 4}},                // DD6A LD IXl,D
    {ld_r_r, NULL, {2, 8, 2, 9, 5}},                // DD6B LD IXl,E
    {ld_r_r, NULL, {2, 8, 2, 9, 8}},                // DD6C LD IXl,IXh
    {nop, NULL, {2, 8, 2}},                         // DD6D LD IXl,IXl
    {ld_r_xy, NULL, {7, 8, 9}},                     // DD6E LD L,(IX+d)
    {ld_r_r, NULL, {2, 8, 2, 9, 0}},                // DD6F LD IXl,A
    {ld_xy_r, NULL, {8, 9, 2}},                     // DD70 LD (IX+d),B
    {ld_xy_r, NULL, {8, 9, 3}},                     // DD71 LD (IX+d),C
    {ld_xy_r, NULL, {8, 9, 4}},                     // DD72 LD (IX+d),D
    {ld_xy_r, NULL, {8, 9, 5}},                     // DD73 LD (IX+d),E
    {ld_xy_r, NULL, {8, 9, 6}},                     // DD74 LD (IX+d),H
    {ld_xy_r, NULL, {8, 9, 7}},                     // DD75 LD (IX+d),L
    {nop, NULL, {1, 4, 1}},                         // DD76
    {ld_xy_r, NULL, {8, 9, 0}},                     // DD77 LD (IX+d),A
    {nop, NULL, {1, 4, 1}},                         // DD78
    {nop, NULL, {1, 4, 1}},                         // DD79
    {nop, NULL, {1, 4, 1}},                         // DD7A
    {nop, NULL, {1, 4, 1}},                         // DD7B
    {ld_r_r, NULL, {2, 8, 2, 0, 8}},                // DD7C LD A,IXh
    {ld_r_r, NULL, {2, 8, 2, 0, 9}},                // DD7D LD A,IXl
    {ld_r_xy, NULL, {0, 8, 9}},                     // DD7E LD A,(IX+d)
    {nop, NULL, {1, 4, 1}},                         // DD7F
    {nop, NULL, {1, 4, 1}},                         // DD80
    {nop, NULL, {1, 4, 1}},                         // DD81
    {nop, NULL, {1, 4, 1}},                         // DD82
    {nop, NULL, {1, 4, 1}},                         // DD83
    {af_r, ADD, {2, 8, 2, 8}},                      // DD84 ADD A,IXh
    {af_r, ADD, {2, 8, 2, 9}},                      // DD85 ADD A,IXl
    {af_xy, ADD, {8, 9}},                           // DD86 ADD A,(IX+d)
    {nop, NULL, {1, 4, 1}},                         // DD87
    {nop, NULL, {1, 4, 1}},                         // DD88
    {nop, NULL, {1, 4, 1}},                         // DD89
    {nop, NULL, {1, 4, 1}},                         // DD8A
    {nop, NULL, {1, 4, 1}},                         // DD8B
    {afc_r, ADC, {2, 8, 2, 8}},                     // DD8C ADC A,IXh
    {afc_r, ADC, {2, 8, 2, 9}},                     // DD8D ADC A,IXl
    {afc_xy, ADC, {8, 9}},                          // DD8E ADC A,(IX+d)
    {nop, NULL, {1, 4, 1}},                         // DD8F
    {nop, NULL, {1, 4, 1}},                         // DD90
    {nop, NULL, {1, 4, 1}},                         // DD91
    {nop, NULL, {1, 4, 1}},                         // DD92
    {nop, NULL, {1, 4, 1}},                         // DD93
    {af_r, SUB, {2, 8, 2, 8}},                      // DD94 SUB IXh
    {af_r, SUB, {2, 8, 2, 9}},                      // DD95 SUB IXl
    {af_xy, SUB, {8, 9}},                           // DD96 SUB (IX+d)
    {nop, NULL, {1, 4, 1}},                         // DD97
    {nop, NULL, {1, 4, 1}},                         // DD98
    {nop, NULL, {1, 4, 1}},                         // DD99
    {nop, NULL, {1, 4, 1}},                         // DD9A
    {nop, NULL, {1, 4, 1}},                         // DD9B
    {afc_r, SBC, {2, 8, 2, 8}},                     // DD9C SBC A,IXh
    {afc_r, SBC, {2, 8, 2, 9}},                     // DD9D SBC A,IXl
    {afc_xy, SBC, {8, 9}},                          // DD9E SBC A,(IX+d)
    {nop, NULL, {1, 4, 1}},                         // DD9F
    {nop, NULL, {1, 4, 1}},                         // DDA0
    {nop, NULL, {1, 4, 1}},                         // DDA1
    {nop, NULL, {1, 4, 1}},                         // DDA2
    {nop, NULL, {1, 4, 1}},                         // DDA3
    {af_r, AND, {2, 8, 2, 8}},                      // DDA4 AND IXh
    {af_r, AND, {2, 8, 2, 9}},                      // DDA5 AND IXl
    {af_xy, AND, {8, 9}},                           // DDA6 AND (IX+d)
    {nop, NULL, {1, 4, 1}},                         // DDA7
    {nop, NULL, {1, 4, 1}},                         // DDA8
    {nop, NULL, {1, 4, 1}},                         // DDA9
    {nop, NULL, {1, 4, 1}},                         // DDAA
    {nop, NULL, {1, 4, 1}},                         // DDAB
    {af_r, XOR, {2, 8, 2, 8}},                      // DDAC XOR IXh
    {af_r, XOR, {2, 8, 2, 9}},                      // DDAD XOR IXl
    {af_xy, XOR, {8, 9}},                           // DDAE XOR (IX+d)
    {nop, NULL, {1, 4, 1}},                         // DDAF
    {nop, NULL, {1, 4, 1}},                         // DDB0
    {nop, NULL, {1, 4, 1}},                         // DDB1
    {nop, NULL, {1, 4, 1}},                         // DDB2
    {nop, NULL, {1, 4, 1}},                         // DDB3
    {af_r, OR, {2, 8, 2, 8}},                       // DDB4 OR IXh
    {af_r, OR, {2, 8, 2, 9}},                       // DDB5 OR IXl
    {af_xy, OR, {8, 9}},                            // DDB6 OR (IX+d)
    {nop, NULL, {1, 4, 1}},                         // DDB7
    {nop, NULL, {1, 4, 1}},                         // DDB8
    {nop, NULL, {1, 4, 1}},                         // DDB9
    {nop, NULL, {1, 4, 1}},                         // DDBA
    {nop, NULL, {1, 4, 1}},                         // DDBB
    {af_r, CP, {2, 8, 2, 8}},                       // DDBC CP IXh
    {af_r, CP, {2, 8, 2, 9}},                       // DDBD CP IXl
    {af_xy, CP, {8, 9}},                            // DDBE CP (IX+d)
    {nop, NULL, {1, 4, 1}},                         // DDBF
    {nop, NULL, {1, 4, 1}},                         // DDC0
    {nop, NULL, {1, 4, 1}},                         // DDC1
    {nop, NULL, {1, 4, 1}},                         // DDC2
    {nop, NULL, {1, 4, 1}},                         // DDC3
    {nop, NULL, {1, 4, 1}},                         // DDC4
    {nop, NULL, {1, 4, 1}},                         // DDC5
    {nop, NULL, {1, 4, 1}},                         // DDC6
    {nop, NULL, {1, 4, 1}},                         // DDC7
    {nop, NULL, {1, 4, 1}},                         // DDC8
    {nop, NULL, {1, 4, 1}},                         // DDC9
    {nop, NULL, {1, 4, 1}},                         // DDCA
    {NULL, NULL, {0}},                              // DDCB prefix
    {nop, NULL, {1, 4, 1}},                         // DDCC
    {nop, NULL, {1, 4, 1}},                         // DDCD
    {nop, NULL, {1, 4, 1}},                         // DDCE
    {nop, NULL, {1, 4, 1}},                         // DDCF
    {nop, NULL, {1, 4, 1}},                         // DDD0
    {nop, NULL, {1, 4, 1}},                         // DDD1
    {nop, NULL, {1, 4, 1}},                         // DDD2
    {nop, NULL, {1, 4, 1}},                         // DDD3
    {nop, NULL, {1, 4, 1}},                         // DDD4
    {nop, NULL, {1, 4, 1}},                         // DDD5
    {nop, NULL, {1, 4, 1}},                         // DDD6
    {nop, NULL, {1, 4, 1}},                         // DDD7
    {nop, NULL, {1, 4, 1}},                         // DDD8
    {nop, NULL, {1, 4, 1}},                         // DDD9
    {nop, NULL, {1, 4, 1}},                         // DDDA
    {nop, NULL, {1, 4, 1}},                         // DDDB
    {nop, NULL, {1, 4, 1}},                         // DDDC
    {nop, NULL, {1, 4, 1}},                         // DDDD
    {nop, NULL, {1, 4, 1}},                         // DDDE
    {nop, NULL, {1, 4, 1}},                         // DDDF
    {nop, NULL, {1, 4, 1}},                         // DDE0
    {pop, NULL, {2, 14, 2, 8, 9}},                  // DDE1 POP IX
    {nop, NULL, {1, 4, 1}},                         // DDE2
    {ex_sp, NULL, {2, 23, 2, 8, 9}},                // DDE3 EX (SP),IX
    {nop, NULL, {1, 4, 1}},                         // DDE4
    {push, NULL, {2, 15, 2, 8, 9}},                 // DDE5 PUSH IX
    {nop, NULL, {1, 4, 1}},                         // DDE6
    {nop, NULL, {1, 4, 1}},                         // DDE7
    {nop, NULL, {1, 4, 1}},                         // DDE8
    {jp_rr, NULL, {2, 8, 8, 9}},                    // DDE9 JP (IX)
    {nop, NULL, {1, 4, 1}},                         // DDEA
    {nop, NULL, {1, 4, 1}},                         // DDEB
    {nop, NULL, {1, 4, 1}},                         // DDEC
    {nop, NULL, {1, 4, 1}},                         // DDED
    {nop, NULL, {1, 4, 1}},                         // DDEE
    {nop, NULL, {1, 4, 1}},                         // DDEF
    {nop, NULL, {1, 4, 1}},                         // DDF0
    {nop, NULL, {1, 4, 1}},                         // DDF1
    {nop, NULL, {1, 4, 1}},                         // DDF2
    {nop, NULL, {1, 4, 1}},                         // DDF3
    {nop, NULL, {1, 4, 1}},                         // DDF4
    {nop, NULL, {1, 4, 1}},                         // DDF5
    {nop, NULL, {1, 4, 1}},                         // DDF6
    {nop, NULL, {1, 4, 1}},                         // DDF7
    {nop, NULL, {1, 4, 1}},                         // DDF8
    {ld_sp_rr, NULL, {2, 10, 2, 8, 9}},             // DDF9 LD SP,IX
    {nop, NULL, {1, 4, 1}},                         // DDFA
    {nop, NULL, {1, 4, 1}},                         // DDFB
    {nop, NULL, {1, 4, 1}},                         // DDFC
    {nop, NULL, {1, 4, 1}},                         // DDFD
    {nop, NULL, {1, 4, 1}},                         // DDFE
    {nop, NULL, {1, 4, 1}},                         // DDFF
};

static OpcodeFunction after_FD[256] = {
    {nop, NULL, {1, 4, 1}},                         // FD00
    {nop, NULL, {1, 4, 1}},                         // FD01
    {nop, NULL, {1, 4, 1}},                         // FD02
    {nop, NULL, {1, 4, 1}},                         // FD03
    {nop, NULL, {1, 4, 1}},                         // FD04
    {nop, NULL, {1, 4, 1}},                         // FD05
    {nop, NULL, {1, 4, 1}},                         // FD06
    {nop, NULL, {1, 4, 1}},                         // FD07
    {nop, NULL, {1, 4, 1}},                         // FD08
    {add_rr, NULL, {2, 15, 2, 10, 11, 2, 3}},       // FD09 ADD IY,BC
    {nop, NULL, {1, 4, 1}},                         // FD0A
    {nop, NULL, {1, 4, 1}},                         // FD0B
    {nop, NULL, {1, 4, 1}},                         // FD0C
    {nop, NULL, {1, 4, 1}},                         // FD0D
    {nop, NULL, {1, 4, 1}},                         // FD0E
    {nop, NULL, {1, 4, 1}},                         // FD0F
    {nop, NULL, {1, 4, 1}},                         // FD10
    {nop, NULL, {1, 4, 1}},                         // FD11
    {nop, NULL, {1, 4, 1}},                         // FD12
    {nop, NULL, {1, 4, 1}},                         // FD13
    {nop, NULL, {1, 4, 1}},                         // FD14
    {nop, NULL, {1, 4, 1}},                         // FD15
    {nop, NULL, {1, 4, 1}},                         // FD16
    {nop, NULL, {1, 4, 1}},                         // FD17
    {nop, NULL, {1, 4, 1}},                         // FD18
    {add_rr, NULL, {2, 15, 2, 10, 11, 4, 5}},       // FD19 ADD IY,DE
    {nop, NULL, {1, 4, 1}},                         // FD1A
    {nop, NULL, {1, 4, 1}},                         // FD1B
    {nop, NULL, {1, 4, 1}},                         // FD1C
    {nop, NULL, {1, 4, 1}},                         // FD1D
    {nop, NULL, {1, 4, 1}},                         // FD1E
    {nop, NULL, {1, 4, 1}},                         // FD1F
    {nop, NULL, {1, 4, 1}},                         // FD20
    {ld_rr_nn, NULL, {2, 14, 4, 10, 11}},           // FD21 LD IY,nn
    {ld_mm_rr, NULL, {2, 20, 4, 10, 11}},           // FD22 LD (nn),IY
    {inc_dec_rr, NULL, {2, 10, 2, 1, 10, 11}},      // FD23 INC IY
    {fc_r, INC, {2, 8, 2, 10}},                     // FD24 INC IYh
    {fc_r, DEC, {2, 8, 2, 10}},                     // FD25 DEC IYh
    {ld_r_n, NULL, {2, 11, 3, 10}},                 // FD26 LD IYh,n
    {nop, NULL, {1, 4, 1}},                         // FD27
    {nop, NULL, {1, 4, 1}},                         // FD28
    {add_rr, NULL, {2, 15, 2, 10, 11, 10, 11}},     // FD29 ADD IY,IY
    {ld_rr_mm, NULL, {2, 20, 4, 10, 11}},           // FD2A LD IY,(nn)
    {inc_dec_rr, NULL, {2, 10, 2, -1, 10, 11}},     // FD2B DEC IY
    {fc_r, INC, {2, 8, 2, 11}},                     // FD2C INC IYl
    {fc_r, DEC, {2, 8, 2, 11}},                     // FD2D DEC IYl
    {ld_r_n, NULL, {2, 11, 3, 11}},                 // FD2E LD IYl,n
    {nop, NULL, {1, 4, 1}},                         // FD2F
    {nop, NULL, {1, 4, 1}},                         // FD30
    {nop, NULL, {1, 4, 1}},                         // FD31
    {nop, NULL, {1, 4, 1}},                         // FD32
    {nop, NULL, {1, 4, 1}},                         // FD33
    {fc_xy, INC, {3, 10, 11, -1}},                  // FD34 INC (IY+d)
    {fc_xy, DEC, {3, 10, 11, -1}},                  // FD35 DEC (IY+d)
    {ld_xy_n, NULL, {10, 11}},                      // FD36 LD (IY+d),n
    {nop, NULL, {1, 4, 1}},                         // FD37
    {nop, NULL, {1, 4, 1}},                         // FD38
    {add_rr, NULL, {2, 15, 2, 10, 11, 13, 12}},     // FD39 ADD IY,SP
    {nop, NULL, {1, 4, 1}},                         // FD3A
    {nop, NULL, {1, 4, 1}},                         // FD3B
    {nop, NULL, {1, 4, 1}},                         // FD3C
    {nop, NULL, {1, 4, 1}},                         // FD3D
    {nop, NULL, {1, 4, 1}},                         // FD3E
    {nop, NULL, {1, 4, 1}},                         // FD3F
    {nop, NULL, {1, 4, 1}},                         // FD40
    {nop, NULL, {1, 4, 1}},                         // FD41
    {nop, NULL, {1, 4, 1}},                         // FD42
    {nop, NULL, {1, 4, 1}},                         // FD43
    {ld_r_r, NULL, {2, 8, 2, 2, 10}},               // FD44 LD B,IYh
    {ld_r_r, NULL, {2, 8, 2, 2, 11}},               // FD45 LD B,IYl
    {ld_r_xy, NULL, {2, 10, 11}},                   // FD46 LD B,(IY+d)
    {nop, NULL, {1, 4, 1}},                         // FD47
    {nop, NULL, {1, 4, 1}},                         // FD48
    {nop, NULL, {1, 4, 1}},                         // FD49
    {nop, NULL, {1, 4, 1}},                         // FD4A
    {nop, NULL, {1, 4, 1}},                         // FD4B
    {ld_r_r, NULL, {2, 8, 2, 3, 10}},               // FD4C LD C,IYh
    {ld_r_r, NULL, {2, 8, 2, 3, 11}},               // FD4D LD C,IYl
    {ld_r_xy, NULL, {3, 10, 11}},                   // FD4E LD C,(IY+d)
    {nop, NULL, {1, 4, 1}},                         // FD4F
    {nop, NULL, {1, 4, 1}},                         // FD50
    {nop, NULL, {1, 4, 1}},                         // FD51
    {nop, NULL, {1, 4, 1}},                         // FD52
    {nop, NULL, {1, 4, 1}},                         // FD53
    {ld_r_r, NULL, {2, 8, 2, 4, 10}},               // FD54 LD D,IYh
    {ld_r_r, NULL, {2, 8, 2, 4, 11}},               // FD55 LD D,IYl
    {ld_r_xy, NULL, {4, 10, 11}},                   // FD56 LD D,(IY+d)
    {nop, NULL, {1, 4, 1}},                         // FD57
    {nop, NULL, {1, 4, 1}},                         // FD58
    {nop, NULL, {1, 4, 1}},                         // FD59
    {nop, NULL, {1, 4, 1}},                         // FD5A
    {nop, NULL, {1, 4, 1}},                         // FD5B
    {ld_r_r, NULL, {2, 8, 2, 5, 10}},               // FD5C LD E,IYh
    {ld_r_r, NULL, {2, 8, 2, 5, 11}},               // FD5D LD E,IYl
    {ld_r_xy, NULL, {5, 10, 11}},                   // FD5E LD E,(IY+d)
    {nop, NULL, {1, 4, 1}},                         // FD5F
    {ld_r_r, NULL, {2, 8, 2, 10, 2}},               // FD60 LD IYh,B
    {ld_r_r, NULL, {2, 8, 2, 10, 3}},               // FD61 LD IYh,C
    {ld_r_r, NULL, {2, 8, 2, 10, 4}},               // FD62 LD IYh,D
    {ld_r_r, NULL, {2, 8, 2, 10, 5}},               // FD63 LD IYh,E
    {nop, NULL, {2, 8, 2}},                         // FD64 LD IYh,IYh
    {ld_r_r, NULL, {2, 8, 2, 10, 11}},              // FD65 LD IYh,IYl
    {ld_r_xy, NULL, {6, 10, 11}},                   // FD66 LD H,(IY+d)
    {ld_r_r, NULL, {2, 8, 2, 10, 0}},               // FD67 LD IYh,A
    {ld_r_r, NULL, {2, 8, 2, 11, 2}},               // FD68 LD IYl,B
    {ld_r_r, NULL, {2, 8, 2, 11, 3}},               // FD69 LD IYl,C
    {ld_r_r, NULL, {2, 8, 2, 11, 4}},               // FD6A LD IYl,D
    {ld_r_r, NULL, {2, 8, 2, 11, 5}},               // FD6B LD IYl,E
    {ld_r_r, NULL, {2, 8, 2, 11, 10}},              // FD6C LD IYl,IYh
    {nop, NULL, {2, 8, 2}},                         // FD6D LD IYl,IYl
    {ld_r_xy, NULL, {7, 10, 11}},                   // FD6E LD L,(IY+d)
    {ld_r_r, NULL, {2, 8, 2, 11, 0}},               // FD6F LD IYl,A
    {ld_xy_r, NULL, {10, 11, 2}},                   // FD70 LD (IY+d),B
    {ld_xy_r, NULL, {10, 11, 3}},                   // FD71 LD (IY+d),C
    {ld_xy_r, NULL, {10, 11, 4}},                   // FD72 LD (IY+d),D
    {ld_xy_r, NULL, {10, 11, 5}},                   // FD73 LD (IY+d),E
    {ld_xy_r, NULL, {10, 11, 6}},                   // FD74 LD (IY+d),H
    {ld_xy_r, NULL, {10, 11, 7}},                   // FD75 LD (IY+d),L
    {nop, NULL, {1, 4, 1}},                         // FD76
    {ld_xy_r, NULL, {10, 11, 0}},                   // FD77 LD (IY+d),A
    {nop, NULL, {1, 4, 1}},                         // FD78
    {nop, NULL, {1, 4, 1}},                         // FD79
    {nop, NULL, {1, 4, 1}},                         // FD7A
    {nop, NULL, {1, 4, 1}},                         // FD7B
    {ld_r_r, NULL, {2, 8, 2, 0, 10}},               // FD7C LD A,IYh
    {ld_r_r, NULL, {2, 8, 2, 0, 11}},               // FD7D LD A,IYl
    {ld_r_xy, NULL, {0, 10, 11}},                   // FD7E LD A,(IY+d)
    {nop, NULL, {1, 4, 1}},                         // FD7F
    {nop, NULL, {1, 4, 1}},                         // FD80
    {nop, NULL, {1, 4, 1}},                         // FD81
    {nop, NULL, {1, 4, 1}},                         // FD82
    {nop, NULL, {1, 4, 1}},                         // FD83
    {af_r, ADD, {2, 8, 2, 10}},                     // FD84 ADD A,IYh
    {af_r, ADD, {2, 8, 2, 11}},                     // FD85 ADD A,IYl
    {af_xy, ADD, {10, 11}},                         // FD86 ADD A,(IY+d)
    {nop, NULL, {1, 4, 1}},                         // FD87
    {nop, NULL, {1, 4, 1}},                         // FD88
    {nop, NULL, {1, 4, 1}},                         // FD89
    {nop, NULL, {1, 4, 1}},                         // FD8A
    {nop, NULL, {1, 4, 1}},                         // FD8B
    {afc_r, ADC, {2, 8, 2, 10}},                    // FD8C ADC A,IYh
    {afc_r, ADC, {2, 8, 2, 11}},                    // FD8D ADC A,IYl
    {afc_xy, ADC, {10, 11}},                        // FD8E ADC A,(IY+d)
    {nop, NULL, {1, 4, 1}},                         // FD8F
    {nop, NULL, {1, 4, 1}},                         // FD90
    {nop, NULL, {1, 4, 1}},                         // FD91
    {nop, NULL, {1, 4, 1}},                         // FD92
    {nop, NULL, {1, 4, 1}},                         // FD93
    {af_r, SUB, {2, 8, 2, 10}},                     // FD94 SUB IYh
    {af_r, SUB, {2, 8, 2, 11}},                     // FD95 SUB IYl
    {af_xy, SUB, {10, 11}},                         // FD96 SUB (IY+d)
    {nop, NULL, {1, 4, 1}},                         // FD97
    {nop, NULL, {1, 4, 1}},                         // FD98
    {nop, NULL, {1, 4, 1}},                         // FD99
    {nop, NULL, {1, 4, 1}},                         // FD9A
    {nop, NULL, {1, 4, 1}},                         // FD9B
    {afc_r, SBC, {2, 8, 2, 10}},                    // FD9C SBC A,IYh
    {afc_r, SBC, {2, 8, 2, 11}},                    // FD9D SBC A,IYl
    {afc_xy, SBC, {10, 11}},                        // FD9E SBC A,(IY+d)
    {nop, NULL, {1, 4, 1}},                         // FD9F
    {nop, NULL, {1, 4, 1}},                         // FDA0
    {nop, NULL, {1, 4, 1}},                         // FDA1
    {nop, NULL, {1, 4, 1}},                         // FDA2
    {nop, NULL, {1, 4, 1}},                         // FDA3
    {af_r, AND, {2, 8, 2, 10}},                     // FDA4 AND IYh
    {af_r, AND, {2, 8, 2, 11}},                     // FDA5 AND IYl
    {af_xy, AND, {10, 11}},                         // FDA6 AND (IY+d)
    {nop, NULL, {1, 4, 1}},                         // FDA7
    {nop, NULL, {1, 4, 1}},                         // FDA8
    {nop, NULL, {1, 4, 1}},                         // FDA9
    {nop, NULL, {1, 4, 1}},                         // FDAA
    {nop, NULL, {1, 4, 1}},                         // FDAB
    {af_r, XOR, {2, 8, 2, 10}},                     // FDAC XOR IYh
    {af_r, XOR, {2, 8, 2, 11}},                     // FDAD XOR IYl
    {af_xy, XOR, {10, 11}},                         // FDAE XOR (IY+d)
    {nop, NULL, {1, 4, 1}},                         // FDAF
    {nop, NULL, {1, 4, 1}},                         // FDB0
    {nop, NULL, {1, 4, 1}},                         // FDB1
    {nop, NULL, {1, 4, 1}},                         // FDB2
    {nop, NULL, {1, 4, 1}},                         // FDB3
    {af_r, OR, {2, 8, 2, 10}},                      // FDB4 OR IYh
    {af_r, OR, {2, 8, 2, 11}},                      // FDB5 OR IYl
    {af_xy, OR, {10, 11}},                          // FDB6 OR (IY+d)
    {nop, NULL, {1, 4, 1}},                         // FDB7
    {nop, NULL, {1, 4, 1}},                         // FDB8
    {nop, NULL, {1, 4, 1}},                         // FDB9
    {nop, NULL, {1, 4, 1}},                         // FDBA
    {nop, NULL, {1, 4, 1}},                         // FDBB
    {af_r, CP, {2, 8, 2, 10}},                      // FDBC CP IYh
    {af_r, CP, {2, 8, 2, 11}},                      // FDBD CP IYl
    {af_xy, CP, {10, 11}},                          // FDBE CP (IY+d)
    {nop, NULL, {1, 4, 1}},                         // FDBF
    {nop, NULL, {1, 4, 1}},                         // FDC0
    {nop, NULL, {1, 4, 1}},                         // FDC1
    {nop, NULL, {1, 4, 1}},                         // FDC2
    {nop, NULL, {1, 4, 1}},                         // FDC3
    {nop, NULL, {1, 4, 1}},                         // FDC4
    {nop, NULL, {1, 4, 1}},                         // FDC5
    {nop, NULL, {1, 4, 1}},                         // FDC6
    {nop, NULL, {1, 4, 1}},                         // FDC7
    {nop, NULL, {1, 4, 1}},                         // FDC8
    {nop, NULL, {1, 4, 1}},                         // FDC9
    {nop, NULL, {1, 4, 1}},                         // FDCA
    {NULL, NULL, {0}},                              // FDCB prefix
    {nop, NULL, {1, 4, 1}},                         // FDCC
    {nop, NULL, {1, 4, 1}},                         // FDCD
    {nop, NULL, {1, 4, 1}},                         // FDCE
    {nop, NULL, {1, 4, 1}},                         // FDCF
    {nop, NULL, {1, 4, 1}},                         // FDD0
    {nop, NULL, {1, 4, 1}},                         // FDD1
    {nop, NULL, {1, 4, 1}},                         // FDD2
    {nop, NULL, {1, 4, 1}},                         // FDD3
    {nop, NULL, {1, 4, 1}},                         // FDD4
    {nop, NULL, {1, 4, 1}},                         // FDD5
    {nop, NULL, {1, 4, 1}},                         // FDD6
    {nop, NULL, {1, 4, 1}},                         // FDD7
    {nop, NULL, {1, 4, 1}},                         // FDD8
    {nop, NULL, {1, 4, 1}},                         // FDD9
    {nop, NULL, {1, 4, 1}},                         // FDDA
    {nop, NULL, {1, 4, 1}},                         // FDDB
    {nop, NULL, {1, 4, 1}},                         // FDDC
    {nop, NULL, {1, 4, 1}},                         // FDDD
    {nop, NULL, {1, 4, 1}},                         // FDDE
    {nop, NULL, {1, 4, 1}},                         // FDDF
    {nop, NULL, {1, 4, 1}},                         // FDE0
    {pop, NULL, {2, 14, 2, 10, 11}},                // FDE1 POP IY
    {nop, NULL, {1, 4, 1}},                         // FDE2
    {ex_sp, NULL, {2, 23, 2, 10, 11}},              // FDE3 EX (SP),IY
    {nop, NULL, {1, 4, 1}},                         // FDE4
    {push, NULL, {2, 15, 2, 10, 11}},               // FDE5 PUSH IY
    {nop, NULL, {1, 4, 1}},                         // FDE6
    {nop, NULL, {1, 4, 1}},                         // FDE7
    {nop, NULL, {1, 4, 1}},                         // FDE8
    {jp_rr, NULL, {2, 8, 10, 11}},                  // FDE9 JP (IY)
    {nop, NULL, {1, 4, 1}},                         // FDEA
    {nop, NULL, {1, 4, 1}},                         // FDEB
    {nop, NULL, {1, 4, 1}},                         // FDEC
    {nop, NULL, {1, 4, 1}},                         // FDED
    {nop, NULL, {1, 4, 1}},                         // FDEE
    {nop, NULL, {1, 4, 1}},                         // FDEF
    {nop, NULL, {1, 4, 1}},                         // FDF0
    {nop, NULL, {1, 4, 1}},                         // FDF1
    {nop, NULL, {1, 4, 1}},                         // FDF2
    {nop, NULL, {1, 4, 1}},                         // FDF3
    {nop, NULL, {1, 4, 1}},                         // FDF4
    {nop, NULL, {1, 4, 1}},                         // FDF5
    {nop, NULL, {1, 4, 1}},                         // FDF6
    {nop, NULL, {1, 4, 1}},                         // FDF7
    {nop, NULL, {1, 4, 1}},                         // FDF8
    {ld_sp_rr, NULL, {2, 10, 2, 10, 11}},           // FDF9 LD SP,IY
    {nop, NULL, {1, 4, 1}},                         // FDFA
    {nop, NULL, {1, 4, 1}},                         // FDFB
    {nop, NULL, {1, 4, 1}},                         // FDFC
    {nop, NULL, {1, 4, 1}},                         // FDFD
    {nop, NULL, {1, 4, 1}},                         // FDFE
    {nop, NULL, {1, 4, 1}},                         // FDFF
};

static OpcodeFunction after_DDCB[256] = {
    {f_xy, RLC, {8, 9, 2}},                         // DDCB..00 RLC (IX+d),B
    {f_xy, RLC, {8, 9, 3}},                         // DDCB..01 RLC (IX+d),C
    {f_xy, RLC, {8, 9, 4}},                         // DDCB..02 RLC (IX+d),D
    {f_xy, RLC, {8, 9, 5}},                         // DDCB..03 RLC (IX+d),E
    {f_xy, RLC, {8, 9, 6}},                         // DDCB..04 RLC (IX+d),H
    {f_xy, RLC, {8, 9, 7}},                         // DDCB..05 RLC (IX+d),L
    {f_xy, RLC, {8, 9, -1}},                        // DDCB..06 RLC (IX+d)
    {f_xy, RLC, {8, 9, 0}},                         // DDCB..07 RLC (IX+d),A
    {f_xy, RRC, {8, 9, 2}},                         // DDCB..08 RRC (IX+d),B
    {f_xy, RRC, {8, 9, 3}},                         // DDCB..09 RRC (IX+d),C
    {f_xy, RRC, {8, 9, 4}},                         // DDCB..0A RRC (IX+d),D
    {f_xy, RRC, {8, 9, 5}},                         // DDCB..0B RRC (IX+d),E
    {f_xy, RRC, {8, 9, 6}},                         // DDCB..0C RRC (IX+d),H
    {f_xy, RRC, {8, 9, 7}},                         // DDCB..0D RRC (IX+d),L
    {f_xy, RRC, {8, 9, -1}},                        // DDCB..0E RRC (IX+d)
    {f_xy, RRC, {8, 9, 0}},                         // DDCB..0F RRC (IX+d),A
    {fc_xy, RL, {4, 8, 9, 2}},                      // DDCB..10 RL (IX+d),B
    {fc_xy, RL, {4, 8, 9, 3}},                      // DDCB..11 RL (IX+d),C
    {fc_xy, RL, {4, 8, 9, 4}},                      // DDCB..12 RL (IX+d),D
    {fc_xy, RL, {4, 8, 9, 5}},                      // DDCB..13 RL (IX+d),E
    {fc_xy, RL, {4, 8, 9, 6}},                      // DDCB..14 RL (IX+d),H
    {fc_xy, RL, {4, 8, 9, 7}},                      // DDCB..15 RL (IX+d),L
    {fc_xy, RL, {4, 8, 9, -1}},                     // DDCB..16 RL (IX+d)
    {fc_xy, RL, {4, 8, 9, 0}},                      // DDCB..17 RL (IX+d),A
    {fc_xy, RR, {4, 8, 9, 2}},                      // DDCB..18 RR (IX+d),B
    {fc_xy, RR, {4, 8, 9, 3}},                      // DDCB..19 RR (IX+d),C
    {fc_xy, RR, {4, 8, 9, 4}},                      // DDCB..1A RR (IX+d),D
    {fc_xy, RR, {4, 8, 9, 5}},                      // DDCB..1B RR (IX+d),E
    {fc_xy, RR, {4, 8, 9, 6}},                      // DDCB..1C RR (IX+d),H
    {fc_xy, RR, {4, 8, 9, 7}},                      // DDCB..1D RR (IX+d),L
    {fc_xy, RR, {4, 8, 9, -1}},                     // DDCB..1E RR (IX+d)
    {fc_xy, RR, {4, 8, 9, 0}},                      // DDCB..1F RR (IX+d),A
    {f_xy, SLA, {8, 9, 2}},                         // DDCB..20 SLA (IX+d),B
    {f_xy, SLA, {8, 9, 3}},                         // DDCB..21 SLA (IX+d),C
    {f_xy, SLA, {8, 9, 4}},                         // DDCB..22 SLA (IX+d),D
    {f_xy, SLA, {8, 9, 5}},                         // DDCB..23 SLA (IX+d),E
    {f_xy, SLA, {8, 9, 6}},                         // DDCB..24 SLA (IX+d),H
    {f_xy, SLA, {8, 9, 7}},                         // DDCB..25 SLA (IX+d),L
    {f_xy, SLA, {8, 9, -1}},                        // DDCB..26 SLA (IX+d)
    {f_xy, SLA, {8, 9, 0}},                         // DDCB..27 SLA (IX+d),A
    {f_xy, SRA, {8, 9, 2}},                         // DDCB..28 SRA (IX+d),B
    {f_xy, SRA, {8, 9, 3}},                         // DDCB..29 SRA (IX+d),C
    {f_xy, SRA, {8, 9, 4}},                         // DDCB..2A SRA (IX+d),D
    {f_xy, SRA, {8, 9, 5}},                         // DDCB..2B SRA (IX+d),E
    {f_xy, SRA, {8, 9, 6}},                         // DDCB..2C SRA (IX+d),H
    {f_xy, SRA, {8, 9, 7}},                         // DDCB..2D SRA (IX+d),L
    {f_xy, SRA, {8, 9, -1}},                        // DDCB..2E SRA (IX+d)
    {f_xy, SRA, {8, 9, 0}},                         // DDCB..2F SRA (IX+d),A
    {f_xy, SLL, {8, 9, 2}},                         // DDCB..30 SLL (IX+d),B
    {f_xy, SLL, {8, 9, 3}},                         // DDCB..31 SLL (IX+d),C
    {f_xy, SLL, {8, 9, 4}},                         // DDCB..32 SLL (IX+d),D
    {f_xy, SLL, {8, 9, 5}},                         // DDCB..33 SLL (IX+d),E
    {f_xy, SLL, {8, 9, 6}},                         // DDCB..34 SLL (IX+d),H
    {f_xy, SLL, {8, 9, 7}},                         // DDCB..35 SLL (IX+d),L
    {f_xy, SLL, {8, 9, -1}},                        // DDCB..36 SLL (IX+d)
    {f_xy, SLL, {8, 9, 0}},                         // DDCB..37 SLL (IX+d),A
    {f_xy, SRL, {8, 9, 2}},                         // DDCB..38 SRL (IX+d),B
    {f_xy, SRL, {8, 9, 3}},                         // DDCB..39 SRL (IX+d),C
    {f_xy, SRL, {8, 9, 4}},                         // DDCB..3A SRL (IX+d),D
    {f_xy, SRL, {8, 9, 5}},                         // DDCB..3B SRL (IX+d),E
    {f_xy, SRL, {8, 9, 6}},                         // DDCB..3C SRL (IX+d),H
    {f_xy, SRL, {8, 9, 7}},                         // DDCB..3D SRL (IX+d),L
    {f_xy, SRL, {8, 9, -1}},                        // DDCB..3E SRL (IX+d)
    {f_xy, SRL, {8, 9, 0}},                         // DDCB..3F SRL (IX+d),A
    {bit_xy, NULL, {0, 8, 9}},                      // DDCB..40 BIT 0,(IX+d)
    {bit_xy, NULL, {0, 8, 9}},                      // DDCB..41 BIT 0,(IX+d)
    {bit_xy, NULL, {0, 8, 9}},                      // DDCB..42 BIT 0,(IX+d)
    {bit_xy, NULL, {0, 8, 9}},                      // DDCB..43 BIT 0,(IX+d)
    {bit_xy, NULL, {0, 8, 9}},                      // DDCB..44 BIT 0,(IX+d)
    {bit_xy, NULL, {0, 8, 9}},                      // DDCB..45 BIT 0,(IX+d)
    {bit_xy, NULL, {0, 8, 9}},                      // DDCB..46 BIT 0,(IX+d)
    {bit_xy, NULL, {0, 8, 9}},                      // DDCB..47 BIT 0,(IX+d)
    {bit_xy, NULL, {1, 8, 9}},                      // DDCB..48 BIT 1,(IX+d)
    {bit_xy, NULL, {1, 8, 9}},                      // DDCB..49 BIT 1,(IX+d)
    {bit_xy, NULL, {1, 8, 9}},                      // DDCB..4A BIT 1,(IX+d)
    {bit_xy, NULL, {1, 8, 9}},                      // DDCB..4B BIT 1,(IX+d)
    {bit_xy, NULL, {1, 8, 9}},                      // DDCB..4C BIT 1,(IX+d)
    {bit_xy, NULL, {1, 8, 9}},                      // DDCB..4D BIT 1,(IX+d)
    {bit_xy, NULL, {1, 8, 9}},                      // DDCB..4E BIT 1,(IX+d)
    {bit_xy, NULL, {1, 8, 9}},                      // DDCB..4F BIT 1,(IX+d)
    {bit_xy, NULL, {2, 8, 9}},                      // DDCB..50 BIT 2,(IX+d)
    {bit_xy, NULL, {2, 8, 9}},                      // DDCB..51 BIT 2,(IX+d)
    {bit_xy, NULL, {2, 8, 9}},                      // DDCB..52 BIT 2,(IX+d)
    {bit_xy, NULL, {2, 8, 9}},                      // DDCB..53 BIT 2,(IX+d)
    {bit_xy, NULL, {2, 8, 9}},                      // DDCB..54 BIT 2,(IX+d)
    {bit_xy, NULL, {2, 8, 9}},                      // DDCB..55 BIT 2,(IX+d)
    {bit_xy, NULL, {2, 8, 9}},                      // DDCB..56 BIT 2,(IX+d)
    {bit_xy, NULL, {2, 8, 9}},                      // DDCB..57 BIT 2,(IX+d)
    {bit_xy, NULL, {3, 8, 9}},                      // DDCB..58 BIT 3,(IX+d)
    {bit_xy, NULL, {3, 8, 9}},                      // DDCB..59 BIT 3,(IX+d)
    {bit_xy, NULL, {3, 8, 9}},                      // DDCB..5A BIT 3,(IX+d)
    {bit_xy, NULL, {3, 8, 9}},                      // DDCB..5B BIT 3,(IX+d)
    {bit_xy, NULL, {3, 8, 9}},                      // DDCB..5C BIT 3,(IX+d)
    {bit_xy, NULL, {3, 8, 9}},                      // DDCB..5D BIT 3,(IX+d)
    {bit_xy, NULL, {3, 8, 9}},                      // DDCB..5E BIT 3,(IX+d)
    {bit_xy, NULL, {3, 8, 9}},                      // DDCB..5F BIT 3,(IX+d)
    {bit_xy, NULL, {4, 8, 9}},                      // DDCB..60 BIT 4,(IX+d)
    {bit_xy, NULL, {4, 8, 9}},                      // DDCB..61 BIT 4,(IX+d)
    {bit_xy, NULL, {4, 8, 9}},                      // DDCB..62 BIT 4,(IX+d)
    {bit_xy, NULL, {4, 8, 9}},                      // DDCB..63 BIT 4,(IX+d)
    {bit_xy, NULL, {4, 8, 9}},                      // DDCB..64 BIT 4,(IX+d)
    {bit_xy, NULL, {4, 8, 9}},                      // DDCB..65 BIT 4,(IX+d)
    {bit_xy, NULL, {4, 8, 9}},                      // DDCB..66 BIT 4,(IX+d)
    {bit_xy, NULL, {4, 8, 9}},                      // DDCB..67 BIT 4,(IX+d)
    {bit_xy, NULL, {5, 8, 9}},                      // DDCB..68 BIT 5,(IX+d)
    {bit_xy, NULL, {5, 8, 9}},                      // DDCB..69 BIT 5,(IX+d)
    {bit_xy, NULL, {5, 8, 9}},                      // DDCB..6A BIT 5,(IX+d)
    {bit_xy, NULL, {5, 8, 9}},                      // DDCB..6B BIT 5,(IX+d)
    {bit_xy, NULL, {5, 8, 9}},                      // DDCB..6C BIT 5,(IX+d)
    {bit_xy, NULL, {5, 8, 9}},                      // DDCB..6D BIT 5,(IX+d)
    {bit_xy, NULL, {5, 8, 9}},                      // DDCB..6E BIT 5,(IX+d)
    {bit_xy, NULL, {5, 8, 9}},                      // DDCB..6F BIT 5,(IX+d)
    {bit_xy, NULL, {6, 8, 9}},                      // DDCB..70 BIT 6,(IX+d)
    {bit_xy, NULL, {6, 8, 9}},                      // DDCB..71 BIT 6,(IX+d)
    {bit_xy, NULL, {6, 8, 9}},                      // DDCB..72 BIT 6,(IX+d)
    {bit_xy, NULL, {6, 8, 9}},                      // DDCB..73 BIT 6,(IX+d)
    {bit_xy, NULL, {6, 8, 9}},                      // DDCB..74 BIT 6,(IX+d)
    {bit_xy, NULL, {6, 8, 9}},                      // DDCB..75 BIT 6,(IX+d)
    {bit_xy, NULL, {6, 8, 9}},                      // DDCB..76 BIT 6,(IX+d)
    {bit_xy, NULL, {6, 8, 9}},                      // DDCB..77 BIT 6,(IX+d)
    {bit_xy, NULL, {7, 8, 9}},                      // DDCB..78 BIT 7,(IX+d)
    {bit_xy, NULL, {7, 8, 9}},                      // DDCB..79 BIT 7,(IX+d)
    {bit_xy, NULL, {7, 8, 9}},                      // DDCB..7A BIT 7,(IX+d)
    {bit_xy, NULL, {7, 8, 9}},                      // DDCB..7B BIT 7,(IX+d)
    {bit_xy, NULL, {7, 8, 9}},                      // DDCB..7C BIT 7,(IX+d)
    {bit_xy, NULL, {7, 8, 9}},                      // DDCB..7D BIT 7,(IX+d)
    {bit_xy, NULL, {7, 8, 9}},                      // DDCB..7E BIT 7,(IX+d)
    {bit_xy, NULL, {7, 8, 9}},                      // DDCB..7F BIT 7,(IX+d)
    {res_xy, NULL, {254, 8, 9, 2}},                 // DDCB..80 RES 0,(IX+d),B
    {res_xy, NULL, {254, 8, 9, 3}},                 // DDCB..81 RES 0,(IX+d),C
    {res_xy, NULL, {254, 8, 9, 4}},                 // DDCB..82 RES 0,(IX+d),D
    {res_xy, NULL, {254, 8, 9, 5}},                 // DDCB..83 RES 0,(IX+d),E
    {res_xy, NULL, {254, 8, 9, 6}},                 // DDCB..84 RES 0,(IX+d),H
    {res_xy, NULL, {254, 8, 9, 7}},                 // DDCB..85 RES 0,(IX+d),L
    {res_xy, NULL, {254, 8, 9, -1}},                // DDCB..86 RES 0,(IX+d)
    {res_xy, NULL, {254, 8, 9, 0}},                 // DDCB..87 RES 0,(IX+d),A
    {res_xy, NULL, {253, 8, 9, 2}},                 // DDCB..88 RES 1,(IX+d),B
    {res_xy, NULL, {253, 8, 9, 3}},                 // DDCB..89 RES 1,(IX+d),C
    {res_xy, NULL, {253, 8, 9, 4}},                 // DDCB..8A RES 1,(IX+d),D
    {res_xy, NULL, {253, 8, 9, 5}},                 // DDCB..8B RES 1,(IX+d),E
    {res_xy, NULL, {253, 8, 9, 6}},                 // DDCB..8C RES 1,(IX+d),H
    {res_xy, NULL, {253, 8, 9, 7}},                 // DDCB..8D RES 1,(IX+d),L
    {res_xy, NULL, {253, 8, 9, -1}},                // DDCB..8E RES 1,(IX+d)
    {res_xy, NULL, {253, 8, 9, 0}},                 // DDCB..8F RES 1,(IX+d),A
    {res_xy, NULL, {251, 8, 9, 2}},                 // DDCB..90 RES 2,(IX+d),B
    {res_xy, NULL, {251, 8, 9, 3}},                 // DDCB..91 RES 2,(IX+d),C
    {res_xy, NULL, {251, 8, 9, 4}},                 // DDCB..92 RES 2,(IX+d),D
    {res_xy, NULL, {251, 8, 9, 5}},                 // DDCB..93 RES 2,(IX+d),E
    {res_xy, NULL, {251, 8, 9, 6}},                 // DDCB..94 RES 2,(IX+d),H
    {res_xy, NULL, {251, 8, 9, 7}},                 // DDCB..95 RES 2,(IX+d),L
    {res_xy, NULL, {251, 8, 9, -1}},                // DDCB..96 RES 2,(IX+d)
    {res_xy, NULL, {251, 8, 9, 0}},                 // DDCB..97 RES 2,(IX+d),A
    {res_xy, NULL, {247, 8, 9, 2}},                 // DDCB..98 RES 3,(IX+d),B
    {res_xy, NULL, {247, 8, 9, 3}},                 // DDCB..99 RES 3,(IX+d),C
    {res_xy, NULL, {247, 8, 9, 4}},                 // DDCB..9A RES 3,(IX+d),D
    {res_xy, NULL, {247, 8, 9, 5}},                 // DDCB..9B RES 3,(IX+d),E
    {res_xy, NULL, {247, 8, 9, 6}},                 // DDCB..9C RES 3,(IX+d),H
    {res_xy, NULL, {247, 8, 9, 7}},                 // DDCB..9D RES 3,(IX+d),L
    {res_xy, NULL, {247, 8, 9, -1}},                // DDCB..9E RES 3,(IX+d)
    {res_xy, NULL, {247, 8, 9, 0}},                 // DDCB..9F RES 3,(IX+d),A
    {res_xy, NULL, {239, 8, 9, 2}},                 // DDCB..A0 RES 4,(IX+d),B
    {res_xy, NULL, {239, 8, 9, 3}},                 // DDCB..A1 RES 4,(IX+d),C
    {res_xy, NULL, {239, 8, 9, 4}},                 // DDCB..A2 RES 4,(IX+d),D
    {res_xy, NULL, {239, 8, 9, 5}},                 // DDCB..A3 RES 4,(IX+d),E
    {res_xy, NULL, {239, 8, 9, 6}},                 // DDCB..A4 RES 4,(IX+d),H
    {res_xy, NULL, {239, 8, 9, 7}},                 // DDCB..A5 RES 4,(IX+d),L
    {res_xy, NULL, {239, 8, 9, -1}},                // DDCB..A6 RES 4,(IX+d)
    {res_xy, NULL, {239, 8, 9, 0}},                 // DDCB..A7 RES 4,(IX+d),A
    {res_xy, NULL, {223, 8, 9, 2}},                 // DDCB..A8 RES 5,(IX+d),B
    {res_xy, NULL, {223, 8, 9, 3}},                 // DDCB..A9 RES 5,(IX+d),C
    {res_xy, NULL, {223, 8, 9, 4}},                 // DDCB..AA RES 5,(IX+d),D
    {res_xy, NULL, {223, 8, 9, 5}},                 // DDCB..AB RES 5,(IX+d),E
    {res_xy, NULL, {223, 8, 9, 6}},                 // DDCB..AC RES 5,(IX+d),H
    {res_xy, NULL, {223, 8, 9, 7}},                 // DDCB..AD RES 5,(IX+d),L
    {res_xy, NULL, {223, 8, 9, -1}},                // DDCB..AE RES 5,(IX+d)
    {res_xy, NULL, {223, 8, 9, 0}},                 // DDCB..AF RES 5,(IX+d),A
    {res_xy, NULL, {191, 8, 9, 2}},                 // DDCB..B0 RES 6,(IX+d),B
    {res_xy, NULL, {191, 8, 9, 3}},                 // DDCB..B1 RES 6,(IX+d),C
    {res_xy, NULL, {191, 8, 9, 4}},                 // DDCB..B2 RES 6,(IX+d),D
    {res_xy, NULL, {191, 8, 9, 5}},                 // DDCB..B3 RES 6,(IX+d),E
    {res_xy, NULL, {191, 8, 9, 6}},                 // DDCB..B4 RES 6,(IX+d),H
    {res_xy, NULL, {191, 8, 9, 7}},                 // DDCB..B5 RES 6,(IX+d),L
    {res_xy, NULL, {191, 8, 9, -1}},                // DDCB..B6 RES 6,(IX+d)
    {res_xy, NULL, {191, 8, 9, 0}},                 // DDCB..B7 RES 6,(IX+d),A
    {res_xy, NULL, {127, 8, 9, 2}},                 // DDCB..B8 RES 7,(IX+d),B
    {res_xy, NULL, {127, 8, 9, 3}},                 // DDCB..B9 RES 7,(IX+d),C
    {res_xy, NULL, {127, 8, 9, 4}},                 // DDCB..BA RES 7,(IX+d),D
    {res_xy, NULL, {127, 8, 9, 5}},                 // DDCB..BB RES 7,(IX+d),E
    {res_xy, NULL, {127, 8, 9, 6}},                 // DDCB..BC RES 7,(IX+d),H
    {res_xy, NULL, {127, 8, 9, 7}},                 // DDCB..BD RES 7,(IX+d),L
    {res_xy, NULL, {127, 8, 9, -1}},                // DDCB..BE RES 7,(IX+d)
    {res_xy, NULL, {127, 8, 9, 0}},                 // DDCB..BF RES 7,(IX+d),A
    {set_xy, NULL, {1, 8, 9, 2}},                   // DDCB..C0 SET 0,(IX+d),B
    {set_xy, NULL, {1, 8, 9, 3}},                   // DDCB..C1 SET 0,(IX+d),C
    {set_xy, NULL, {1, 8, 9, 4}},                   // DDCB..C2 SET 0,(IX+d),D
    {set_xy, NULL, {1, 8, 9, 5}},                   // DDCB..C3 SET 0,(IX+d),E
    {set_xy, NULL, {1, 8, 9, 6}},                   // DDCB..C4 SET 0,(IX+d),H
    {set_xy, NULL, {1, 8, 9, 7}},                   // DDCB..C5 SET 0,(IX+d),L
    {set_xy, NULL, {1, 8, 9, -1}},                  // DDCB..C6 SET 0,(IX+d)
    {set_xy, NULL, {1, 8, 9, 0}},                   // DDCB..C7 SET 0,(IX+d),A
    {set_xy, NULL, {2, 8, 9, 2}},                   // DDCB..C8 SET 1,(IX+d),B
    {set_xy, NULL, {2, 8, 9, 3}},                   // DDCB..C9 SET 1,(IX+d),C
    {set_xy, NULL, {2, 8, 9, 4}},                   // DDCB..CA SET 1,(IX+d),D
    {set_xy, NULL, {2, 8, 9, 5}},                   // DDCB..CB SET 1,(IX+d),E
    {set_xy, NULL, {2, 8, 9, 6}},                   // DDCB..CC SET 1,(IX+d),H
    {set_xy, NULL, {2, 8, 9, 7}},                   // DDCB..CD SET 1,(IX+d),L
    {set_xy, NULL, {2, 8, 9, -1}},                  // DDCB..CE SET 1,(IX+d)
    {set_xy, NULL, {2, 8, 9, 0}},                   // DDCB..CF SET 1,(IX+d),A
    {set_xy, NULL, {4, 8, 9, 2}},                   // DDCB..D0 SET 2,(IX+d),B
    {set_xy, NULL, {4, 8, 9, 3}},                   // DDCB..D1 SET 2,(IX+d),C
    {set_xy, NULL, {4, 8, 9, 4}},                   // DDCB..D2 SET 2,(IX+d),D
    {set_xy, NULL, {4, 8, 9, 5}},                   // DDCB..D3 SET 2,(IX+d),E
    {set_xy, NULL, {4, 8, 9, 6}},                   // DDCB..D4 SET 2,(IX+d),H
    {set_xy, NULL, {4, 8, 9, 7}},                   // DDCB..D5 SET 2,(IX+d),L
    {set_xy, NULL, {4, 8, 9, -1}},                  // DDCB..D6 SET 2,(IX+d)
    {set_xy, NULL, {4, 8, 9, 0}},                   // DDCB..D7 SET 2,(IX+d),A
    {set_xy, NULL, {8, 8, 9, 2}},                   // DDCB..D8 SET 3,(IX+d),B
    {set_xy, NULL, {8, 8, 9, 3}},                   // DDCB..D9 SET 3,(IX+d),C
    {set_xy, NULL, {8, 8, 9, 4}},                   // DDCB..DA SET 3,(IX+d),D
    {set_xy, NULL, {8, 8, 9, 5}},                   // DDCB..DB SET 3,(IX+d),E
    {set_xy, NULL, {8, 8, 9, 6}},                   // DDCB..DC SET 3,(IX+d),H
    {set_xy, NULL, {8, 8, 9, 7}},                   // DDCB..DD SET 3,(IX+d),L
    {set_xy, NULL, {8, 8, 9, -1}},                  // DDCB..DE SET 3,(IX+d)
    {set_xy, NULL, {8, 8, 9, 0}},                   // DDCB..DF SET 3,(IX+d),A
    {set_xy, NULL, {16, 8, 9, 2}},                  // DDCB..E0 SET 4,(IX+d),B
    {set_xy, NULL, {16, 8, 9, 3}},                  // DDCB..E1 SET 4,(IX+d),C
    {set_xy, NULL, {16, 8, 9, 4}},                  // DDCB..E2 SET 4,(IX+d),D
    {set_xy, NULL, {16, 8, 9, 5}},                  // DDCB..E3 SET 4,(IX+d),E
    {set_xy, NULL, {16, 8, 9, 6}},                  // DDCB..E4 SET 4,(IX+d),H
    {set_xy, NULL, {16, 8, 9, 7}},                  // DDCB..E5 SET 4,(IX+d),L
    {set_xy, NULL, {16, 8, 9, -1}},                 // DDCB..E6 SET 4,(IX+d)
    {set_xy, NULL, {16, 8, 9, 0}},                  // DDCB..E7 SET 4,(IX+d),A
    {set_xy, NULL, {32, 8, 9, 2}},                  // DDCB..E8 SET 5,(IX+d),B
    {set_xy, NULL, {32, 8, 9, 3}},                  // DDCB..E9 SET 5,(IX+d),C
    {set_xy, NULL, {32, 8, 9, 4}},                  // DDCB..EA SET 5,(IX+d),D
    {set_xy, NULL, {32, 8, 9, 5}},                  // DDCB..EB SET 5,(IX+d),E
    {set_xy, NULL, {32, 8, 9, 6}},                  // DDCB..EC SET 5,(IX+d),H
    {set_xy, NULL, {32, 8, 9, 7}},                  // DDCB..ED SET 5,(IX+d),L
    {set_xy, NULL, {32, 8, 9, -1}},                 // DDCB..EE SET 5,(IX+d)
    {set_xy, NULL, {32, 8, 9, 0}},                  // DDCB..EF SET 5,(IX+d),A
    {set_xy, NULL, {64, 8, 9, 2}},                  // DDCB..F0 SET 6,(IX+d),B
    {set_xy, NULL, {64, 8, 9, 3}},                  // DDCB..F1 SET 6,(IX+d),C
    {set_xy, NULL, {64, 8, 9, 4}},                  // DDCB..F2 SET 6,(IX+d),D
    {set_xy, NULL, {64, 8, 9, 5}},                  // DDCB..F3 SET 6,(IX+d),E
    {set_xy, NULL, {64, 8, 9, 6}},                  // DDCB..F4 SET 6,(IX+d),H
    {set_xy, NULL, {64, 8, 9, 7}},                  // DDCB..F5 SET 6,(IX+d),L
    {set_xy, NULL, {64, 8, 9, -1}},                 // DDCB..F6 SET 6,(IX+d)
    {set_xy, NULL, {64, 8, 9, 0}},                  // DDCB..F7 SET 6,(IX+d),A
    {set_xy, NULL, {128, 8, 9, 2}},                 // DDCB..F8 SET 7,(IX+d),B
    {set_xy, NULL, {128, 8, 9, 3}},                 // DDCB..F9 SET 7,(IX+d),C
    {set_xy, NULL, {128, 8, 9, 4}},                 // DDCB..FA SET 7,(IX+d),D
    {set_xy, NULL, {128, 8, 9, 5}},                 // DDCB..FB SET 7,(IX+d),E
    {set_xy, NULL, {128, 8, 9, 6}},                 // DDCB..FC SET 7,(IX+d),H
    {set_xy, NULL, {128, 8, 9, 7}},                 // DDCB..FD SET 7,(IX+d),L
    {set_xy, NULL, {128, 8, 9, -1}},                // DDCB..FE SET 7,(IX+d)
    {set_xy, NULL, {128, 8, 9, 0}},                 // DDCB..FF SET 7,(IX+d),A
};

static OpcodeFunction after_FDCB[256] = {
    {f_xy, RLC, {10, 11, 2}},                       // FDCB..00 RLC (IY+d),B
    {f_xy, RLC, {10, 11, 3}},                       // FDCB..01 RLC (IY+d),C
    {f_xy, RLC, {10, 11, 4}},                       // FDCB..02 RLC (IY+d),D
    {f_xy, RLC, {10, 11, 5}},                       // FDCB..03 RLC (IY+d),E
    {f_xy, RLC, {10, 11, 6}},                       // FDCB..04 RLC (IY+d),H
    {f_xy, RLC, {10, 11, 7}},                       // FDCB..05 RLC (IY+d),L
    {f_xy, RLC, {10, 11, -1}},                      // FDCB..06 RLC (IY+d)
    {f_xy, RLC, {10, 11, 0}},                       // FDCB..07 RLC (IY+d),A
    {f_xy, RRC, {10, 11, 2}},                       // FDCB..08 RRC (IY+d),B
    {f_xy, RRC, {10, 11, 3}},                       // FDCB..09 RRC (IY+d),C
    {f_xy, RRC, {10, 11, 4}},                       // FDCB..0A RRC (IY+d),D
    {f_xy, RRC, {10, 11, 5}},                       // FDCB..0B RRC (IY+d),E
    {f_xy, RRC, {10, 11, 6}},                       // FDCB..0C RRC (IY+d),H
    {f_xy, RRC, {10, 11, 7}},                       // FDCB..0D RRC (IY+d),L
    {f_xy, RRC, {10, 11, -1}},                      // FDCB..0E RRC (IY+d)
    {f_xy, RRC, {10, 11, 0}},                       // FDCB..0F RRC (IY+d),A
    {fc_xy, RL, {4, 10, 11, 2}},                    // FDCB..10 RL (IY+d),B
    {fc_xy, RL, {4, 10, 11, 3}},                    // FDCB..11 RL (IY+d),C
    {fc_xy, RL, {4, 10, 11, 4}},                    // FDCB..12 RL (IY+d),D
    {fc_xy, RL, {4, 10, 11, 5}},                    // FDCB..13 RL (IY+d),E
    {fc_xy, RL, {4, 10, 11, 6}},                    // FDCB..14 RL (IY+d),H
    {fc_xy, RL, {4, 10, 11, 7}},                    // FDCB..15 RL (IY+d),L
    {fc_xy, RL, {4, 10, 11, -1}},                   // FDCB..16 RL (IY+d)
    {fc_xy, RL, {4, 10, 11, 0}},                    // FDCB..17 RL (IY+d),A
    {fc_xy, RR, {4, 10, 11, 2}},                    // FDCB..18 RR (IY+d),B
    {fc_xy, RR, {4, 10, 11, 3}},                    // FDCB..19 RR (IY+d),C
    {fc_xy, RR, {4, 10, 11, 4}},                    // FDCB..1A RR (IY+d),D
    {fc_xy, RR, {4, 10, 11, 5}},                    // FDCB..1B RR (IY+d),E
    {fc_xy, RR, {4, 10, 11, 6}},                    // FDCB..1C RR (IY+d),H
    {fc_xy, RR, {4, 10, 11, 7}},                    // FDCB..1D RR (IY+d),L
    {fc_xy, RR, {4, 10, 11, -1}},                   // FDCB..1E RR (IY+d)
    {fc_xy, RR, {4, 10, 11, 0}},                    // FDCB..1F RR (IY+d),A
    {f_xy, SLA, {10, 11, 2}},                       // FDCB..20 SLA (IY+d),B
    {f_xy, SLA, {10, 11, 3}},                       // FDCB..21 SLA (IY+d),C
    {f_xy, SLA, {10, 11, 4}},                       // FDCB..22 SLA (IY+d),D
    {f_xy, SLA, {10, 11, 5}},                       // FDCB..23 SLA (IY+d),E
    {f_xy, SLA, {10, 11, 6}},                       // FDCB..24 SLA (IY+d),H
    {f_xy, SLA, {10, 11, 7}},                       // FDCB..25 SLA (IY+d),L
    {f_xy, SLA, {10, 11, -1}},                      // FDCB..26 SLA (IY+d)
    {f_xy, SLA, {10, 11, 0}},                       // FDCB..27 SLA (IY+d),A
    {f_xy, SRA, {10, 11, 2}},                       // FDCB..28 SRA (IY+d),B
    {f_xy, SRA, {10, 11, 3}},                       // FDCB..29 SRA (IY+d),C
    {f_xy, SRA, {10, 11, 4}},                       // FDCB..2A SRA (IY+d),D
    {f_xy, SRA, {10, 11, 5}},                       // FDCB..2B SRA (IY+d),E
    {f_xy, SRA, {10, 11, 6}},                       // FDCB..2C SRA (IY+d),H
    {f_xy, SRA, {10, 11, 7}},                       // FDCB..2D SRA (IY+d),L
    {f_xy, SRA, {10, 11, -1}},                      // FDCB..2E SRA (IY+d)
    {f_xy, SRA, {10, 11, 0}},                       // FDCB..2F SRA (IY+d),A
    {f_xy, SLL, {10, 11, 2}},                       // FDCB..30 SLL (IY+d),B
    {f_xy, SLL, {10, 11, 3}},                       // FDCB..31 SLL (IY+d),C
    {f_xy, SLL, {10, 11, 4}},                       // FDCB..32 SLL (IY+d),D
    {f_xy, SLL, {10, 11, 5}},                       // FDCB..33 SLL (IY+d),E
    {f_xy, SLL, {10, 11, 6}},                       // FDCB..34 SLL (IY+d),H
    {f_xy, SLL, {10, 11, 7}},                       // FDCB..35 SLL (IY+d),L
    {f_xy, SLL, {10, 11, -1}},                      // FDCB..36 SLL (IY+d)
    {f_xy, SLL, {10, 11, 0}},                       // FDCB..37 SLL (IY+d),A
    {f_xy, SRL, {10, 11, 2}},                       // FDCB..38 SRL (IY+d),B
    {f_xy, SRL, {10, 11, 3}},                       // FDCB..39 SRL (IY+d),C
    {f_xy, SRL, {10, 11, 4}},                       // FDCB..3A SRL (IY+d),D
    {f_xy, SRL, {10, 11, 5}},                       // FDCB..3B SRL (IY+d),E
    {f_xy, SRL, {10, 11, 6}},                       // FDCB..3C SRL (IY+d),H
    {f_xy, SRL, {10, 11, 7}},                       // FDCB..3D SRL (IY+d),L
    {f_xy, SRL, {10, 11, -1}},                      // FDCB..3E SRL (IY+d)
    {f_xy, SRL, {10, 11, 0}},                       // FDCB..3F SRL (IY+d),A
    {bit_xy, NULL, {0, 10, 11}},                    // FDCB..40 BIT 0,(IY+d)
    {bit_xy, NULL, {0, 10, 11}},                    // FDCB..41 BIT 0,(IY+d)
    {bit_xy, NULL, {0, 10, 11}},                    // FDCB..42 BIT 0,(IY+d)
    {bit_xy, NULL, {0, 10, 11}},                    // FDCB..43 BIT 0,(IY+d)
    {bit_xy, NULL, {0, 10, 11}},                    // FDCB..44 BIT 0,(IY+d)
    {bit_xy, NULL, {0, 10, 11}},                    // FDCB..45 BIT 0,(IY+d)
    {bit_xy, NULL, {0, 10, 11}},                    // FDCB..46 BIT 0,(IY+d)
    {bit_xy, NULL, {0, 10, 11}},                    // FDCB..47 BIT 0,(IY+d)
    {bit_xy, NULL, {1, 10, 11}},                    // FDCB..48 BIT 1,(IY+d)
    {bit_xy, NULL, {1, 10, 11}},                    // FDCB..49 BIT 1,(IY+d)
    {bit_xy, NULL, {1, 10, 11}},                    // FDCB..4A BIT 1,(IY+d)
    {bit_xy, NULL, {1, 10, 11}},                    // FDCB..4B BIT 1,(IY+d)
    {bit_xy, NULL, {1, 10, 11}},                    // FDCB..4C BIT 1,(IY+d)
    {bit_xy, NULL, {1, 10, 11}},                    // FDCB..4D BIT 1,(IY+d)
    {bit_xy, NULL, {1, 10, 11}},                    // FDCB..4E BIT 1,(IY+d)
    {bit_xy, NULL, {1, 10, 11}},                    // FDCB..4F BIT 1,(IY+d)
    {bit_xy, NULL, {2, 10, 11}},                    // FDCB..50 BIT 2,(IY+d)
    {bit_xy, NULL, {2, 10, 11}},                    // FDCB..51 BIT 2,(IY+d)
    {bit_xy, NULL, {2, 10, 11}},                    // FDCB..52 BIT 2,(IY+d)
    {bit_xy, NULL, {2, 10, 11}},                    // FDCB..53 BIT 2,(IY+d)
    {bit_xy, NULL, {2, 10, 11}},                    // FDCB..54 BIT 2,(IY+d)
    {bit_xy, NULL, {2, 10, 11}},                    // FDCB..55 BIT 2,(IY+d)
    {bit_xy, NULL, {2, 10, 11}},                    // FDCB..56 BIT 2,(IY+d)
    {bit_xy, NULL, {2, 10, 11}},                    // FDCB..57 BIT 2,(IY+d)
    {bit_xy, NULL, {3, 10, 11}},                    // FDCB..58 BIT 3,(IY+d)
    {bit_xy, NULL, {3, 10, 11}},                    // FDCB..59 BIT 3,(IY+d)
    {bit_xy, NULL, {3, 10, 11}},                    // FDCB..5A BIT 3,(IY+d)
    {bit_xy, NULL, {3, 10, 11}},                    // FDCB..5B BIT 3,(IY+d)
    {bit_xy, NULL, {3, 10, 11}},                    // FDCB..5C BIT 3,(IY+d)
    {bit_xy, NULL, {3, 10, 11}},                    // FDCB..5D BIT 3,(IY+d)
    {bit_xy, NULL, {3, 10, 11}},                    // FDCB..5E BIT 3,(IY+d)
    {bit_xy, NULL, {3, 10, 11}},                    // FDCB..5F BIT 3,(IY+d)
    {bit_xy, NULL, {4, 10, 11}},                    // FDCB..60 BIT 4,(IY+d)
    {bit_xy, NULL, {4, 10, 11}},                    // FDCB..61 BIT 4,(IY+d)
    {bit_xy, NULL, {4, 10, 11}},                    // FDCB..62 BIT 4,(IY+d)
    {bit_xy, NULL, {4, 10, 11}},                    // FDCB..63 BIT 4,(IY+d)
    {bit_xy, NULL, {4, 10, 11}},                    // FDCB..64 BIT 4,(IY+d)
    {bit_xy, NULL, {4, 10, 11}},                    // FDCB..65 BIT 4,(IY+d)
    {bit_xy, NULL, {4, 10, 11}},                    // FDCB..66 BIT 4,(IY+d)
    {bit_xy, NULL, {4, 10, 11}},                    // FDCB..67 BIT 4,(IY+d)
    {bit_xy, NULL, {5, 10, 11}},                    // FDCB..68 BIT 5,(IY+d)
    {bit_xy, NULL, {5, 10, 11}},                    // FDCB..69 BIT 5,(IY+d)
    {bit_xy, NULL, {5, 10, 11}},                    // FDCB..6A BIT 5,(IY+d)
    {bit_xy, NULL, {5, 10, 11}},                    // FDCB..6B BIT 5,(IY+d)
    {bit_xy, NULL, {5, 10, 11}},                    // FDCB..6C BIT 5,(IY+d)
    {bit_xy, NULL, {5, 10, 11}},                    // FDCB..6D BIT 5,(IY+d)
    {bit_xy, NULL, {5, 10, 11}},                    // FDCB..6E BIT 5,(IY+d)
    {bit_xy, NULL, {5, 10, 11}},                    // FDCB..6F BIT 5,(IY+d)
    {bit_xy, NULL, {6, 10, 11}},                    // FDCB..70 BIT 6,(IY+d)
    {bit_xy, NULL, {6, 10, 11}},                    // FDCB..71 BIT 6,(IY+d)
    {bit_xy, NULL, {6, 10, 11}},                    // FDCB..72 BIT 6,(IY+d)
    {bit_xy, NULL, {6, 10, 11}},                    // FDCB..73 BIT 6,(IY+d)
    {bit_xy, NULL, {6, 10, 11}},                    // FDCB..74 BIT 6,(IY+d)
    {bit_xy, NULL, {6, 10, 11}},                    // FDCB..75 BIT 6,(IY+d)
    {bit_xy, NULL, {6, 10, 11}},                    // FDCB..76 BIT 6,(IY+d)
    {bit_xy, NULL, {6, 10, 11}},                    // FDCB..77 BIT 6,(IY+d)
    {bit_xy, NULL, {7, 10, 11}},                    // FDCB..78 BIT 7,(IY+d)
    {bit_xy, NULL, {7, 10, 11}},                    // FDCB..79 BIT 7,(IY+d)
    {bit_xy, NULL, {7, 10, 11}},                    // FDCB..7A BIT 7,(IY+d)
    {bit_xy, NULL, {7, 10, 11}},                    // FDCB..7B BIT 7,(IY+d)
    {bit_xy, NULL, {7, 10, 11}},                    // FDCB..7C BIT 7,(IY+d)
    {bit_xy, NULL, {7, 10, 11}},                    // FDCB..7D BIT 7,(IY+d)
    {bit_xy, NULL, {7, 10, 11}},                    // FDCB..7E BIT 7,(IY+d)
    {bit_xy, NULL, {7, 10, 11}},                    // FDCB..7F BIT 7,(IY+d)
    {res_xy, NULL, {254, 10, 11, 2}},               // FDCB..80 RES 0,(IY+d),B
    {res_xy, NULL, {254, 10, 11, 3}},               // FDCB..81 RES 0,(IY+d),C
    {res_xy, NULL, {254, 10, 11, 4}},               // FDCB..82 RES 0,(IY+d),D
    {res_xy, NULL, {254, 10, 11, 5}},               // FDCB..83 RES 0,(IY+d),E
    {res_xy, NULL, {254, 10, 11, 6}},               // FDCB..84 RES 0,(IY+d),H
    {res_xy, NULL, {254, 10, 11, 7}},               // FDCB..85 RES 0,(IY+d),L
    {res_xy, NULL, {254, 10, 11, -1}},              // FDCB..86 RES 0,(IY+d)
    {res_xy, NULL, {254, 10, 11, 0}},               // FDCB..87 RES 0,(IY+d),A
    {res_xy, NULL, {253, 10, 11, 2}},               // FDCB..88 RES 1,(IY+d),B
    {res_xy, NULL, {253, 10, 11, 3}},               // FDCB..89 RES 1,(IY+d),C
    {res_xy, NULL, {253, 10, 11, 4}},               // FDCB..8A RES 1,(IY+d),D
    {res_xy, NULL, {253, 10, 11, 5}},               // FDCB..8B RES 1,(IY+d),E
    {res_xy, NULL, {253, 10, 11, 6}},               // FDCB..8C RES 1,(IY+d),H
    {res_xy, NULL, {253, 10, 11, 7}},               // FDCB..8D RES 1,(IY+d),L
    {res_xy, NULL, {253, 10, 11, -1}},              // FDCB..8E RES 1,(IY+d)
    {res_xy, NULL, {253, 10, 11, 0}},               // FDCB..8F RES 1,(IY+d),A
    {res_xy, NULL, {251, 10, 11, 2}},               // FDCB..90 RES 2,(IY+d),B
    {res_xy, NULL, {251, 10, 11, 3}},               // FDCB..91 RES 2,(IY+d),C
    {res_xy, NULL, {251, 10, 11, 4}},               // FDCB..92 RES 2,(IY+d),D
    {res_xy, NULL, {251, 10, 11, 5}},               // FDCB..93 RES 2,(IY+d),E
    {res_xy, NULL, {251, 10, 11, 6}},               // FDCB..94 RES 2,(IY+d),H
    {res_xy, NULL, {251, 10, 11, 7}},               // FDCB..95 RES 2,(IY+d),L
    {res_xy, NULL, {251, 10, 11, -1}},              // FDCB..96 RES 2,(IY+d)
    {res_xy, NULL, {251, 10, 11, 0}},               // FDCB..97 RES 2,(IY+d),A
    {res_xy, NULL, {247, 10, 11, 2}},               // FDCB..98 RES 3,(IY+d),B
    {res_xy, NULL, {247, 10, 11, 3}},               // FDCB..99 RES 3,(IY+d),C
    {res_xy, NULL, {247, 10, 11, 4}},               // FDCB..9A RES 3,(IY+d),D
    {res_xy, NULL, {247, 10, 11, 5}},               // FDCB..9B RES 3,(IY+d),E
    {res_xy, NULL, {247, 10, 11, 6}},               // FDCB..9C RES 3,(IY+d),H
    {res_xy, NULL, {247, 10, 11, 7}},               // FDCB..9D RES 3,(IY+d),L
    {res_xy, NULL, {247, 10, 11, -1}},              // FDCB..9E RES 3,(IY+d)
    {res_xy, NULL, {247, 10, 11, 0}},               // FDCB..9F RES 3,(IY+d),A
    {res_xy, NULL, {239, 10, 11, 2}},               // FDCB..A0 RES 4,(IY+d),B
    {res_xy, NULL, {239, 10, 11, 3}},               // FDCB..A1 RES 4,(IY+d),C
    {res_xy, NULL, {239, 10, 11, 4}},               // FDCB..A2 RES 4,(IY+d),D
    {res_xy, NULL, {239, 10, 11, 5}},               // FDCB..A3 RES 4,(IY+d),E
    {res_xy, NULL, {239, 10, 11, 6}},               // FDCB..A4 RES 4,(IY+d),H
    {res_xy, NULL, {239, 10, 11, 7}},               // FDCB..A5 RES 4,(IY+d),L
    {res_xy, NULL, {239, 10, 11, -1}},              // FDCB..A6 RES 4,(IY+d)
    {res_xy, NULL, {239, 10, 11, 0}},               // FDCB..A7 RES 4,(IY+d),A
    {res_xy, NULL, {223, 10, 11, 2}},               // FDCB..A8 RES 5,(IY+d),B
    {res_xy, NULL, {223, 10, 11, 3}},               // FDCB..A9 RES 5,(IY+d),C
    {res_xy, NULL, {223, 10, 11, 4}},               // FDCB..AA RES 5,(IY+d),D
    {res_xy, NULL, {223, 10, 11, 5}},               // FDCB..AB RES 5,(IY+d),E
    {res_xy, NULL, {223, 10, 11, 6}},               // FDCB..AC RES 5,(IY+d),H
    {res_xy, NULL, {223, 10, 11, 7}},               // FDCB..AD RES 5,(IY+d),L
    {res_xy, NULL, {223, 10, 11, -1}},              // FDCB..AE RES 5,(IY+d)
    {res_xy, NULL, {223, 10, 11, 0}},               // FDCB..AF RES 5,(IY+d),A
    {res_xy, NULL, {191, 10, 11, 2}},               // FDCB..B0 RES 6,(IY+d),B
    {res_xy, NULL, {191, 10, 11, 3}},               // FDCB..B1 RES 6,(IY+d),C
    {res_xy, NULL, {191, 10, 11, 4}},               // FDCB..B2 RES 6,(IY+d),D
    {res_xy, NULL, {191, 10, 11, 5}},               // FDCB..B3 RES 6,(IY+d),E
    {res_xy, NULL, {191, 10, 11, 6}},               // FDCB..B4 RES 6,(IY+d),H
    {res_xy, NULL, {191, 10, 11, 7}},               // FDCB..B5 RES 6,(IY+d),L
    {res_xy, NULL, {191, 10, 11, -1}},              // FDCB..B6 RES 6,(IY+d)
    {res_xy, NULL, {191, 10, 11, 0}},               // FDCB..B7 RES 6,(IY+d),A
    {res_xy, NULL, {127, 10, 11, 2}},               // FDCB..B8 RES 7,(IY+d),B
    {res_xy, NULL, {127, 10, 11, 3}},               // FDCB..B9 RES 7,(IY+d),C
    {res_xy, NULL, {127, 10, 11, 4}},               // FDCB..BA RES 7,(IY+d),D
    {res_xy, NULL, {127, 10, 11, 5}},               // FDCB..BB RES 7,(IY+d),E
    {res_xy, NULL, {127, 10, 11, 6}},               // FDCB..BC RES 7,(IY+d),H
    {res_xy, NULL, {127, 10, 11, 7}},               // FDCB..BD RES 7,(IY+d),L
    {res_xy, NULL, {127, 10, 11, -1}},              // FDCB..BE RES 7,(IY+d)
    {res_xy, NULL, {127, 10, 11, 0}},               // FDCB..BF RES 7,(IY+d),A
    {set_xy, NULL, {1, 10, 11, 2}},                 // FDCB..C0 SET 0,(IY+d),B
    {set_xy, NULL, {1, 10, 11, 3}},                 // FDCB..C1 SET 0,(IY+d),C
    {set_xy, NULL, {1, 10, 11, 4}},                 // FDCB..C2 SET 0,(IY+d),D
    {set_xy, NULL, {1, 10, 11, 5}},                 // FDCB..C3 SET 0,(IY+d),E
    {set_xy, NULL, {1, 10, 11, 6}},                 // FDCB..C4 SET 0,(IY+d),H
    {set_xy, NULL, {1, 10, 11, 7}},                 // FDCB..C5 SET 0,(IY+d),L
    {set_xy, NULL, {1, 10, 11, -1}},                // FDCB..C6 SET 0,(IY+d)
    {set_xy, NULL, {1, 10, 11, 0}},                 // FDCB..C7 SET 0,(IY+d),A
    {set_xy, NULL, {2, 10, 11, 2}},                 // FDCB..C8 SET 1,(IY+d),B
    {set_xy, NULL, {2, 10, 11, 3}},                 // FDCB..C9 SET 1,(IY+d),C
    {set_xy, NULL, {2, 10, 11, 4}},                 // FDCB..CA SET 1,(IY+d),D
    {set_xy, NULL, {2, 10, 11, 5}},                 // FDCB..CB SET 1,(IY+d),E
    {set_xy, NULL, {2, 10, 11, 6}},                 // FDCB..CC SET 1,(IY+d),H
    {set_xy, NULL, {2, 10, 11, 7}},                 // FDCB..CD SET 1,(IY+d),L
    {set_xy, NULL, {2, 10, 11, -1}},                // FDCB..CE SET 1,(IY+d)
    {set_xy, NULL, {2, 10, 11, 0}},                 // FDCB..CF SET 1,(IY+d),A
    {set_xy, NULL, {4, 10, 11, 2}},                 // FDCB..D0 SET 2,(IY+d),B
    {set_xy, NULL, {4, 10, 11, 3}},                 // FDCB..D1 SET 2,(IY+d),C
    {set_xy, NULL, {4, 10, 11, 4}},                 // FDCB..D2 SET 2,(IY+d),D
    {set_xy, NULL, {4, 10, 11, 5}},                 // FDCB..D3 SET 2,(IY+d),E
    {set_xy, NULL, {4, 10, 11, 6}},                 // FDCB..D4 SET 2,(IY+d),H
    {set_xy, NULL, {4, 10, 11, 7}},                 // FDCB..D5 SET 2,(IY+d),L
    {set_xy, NULL, {4, 10, 11, -1}},                // FDCB..D6 SET 2,(IY+d)
    {set_xy, NULL, {4, 10, 11, 0}},                 // FDCB..D7 SET 2,(IY+d),A
    {set_xy, NULL, {8, 10, 11, 2}},                 // FDCB..D8 SET 3,(IY+d),B
    {set_xy, NULL, {8, 10, 11, 3}},                 // FDCB..D9 SET 3,(IY+d),C
    {set_xy, NULL, {8, 10, 11, 4}},                 // FDCB..DA SET 3,(IY+d),D
    {set_xy, NULL, {8, 10, 11, 5}},                 // FDCB..DB SET 3,(IY+d),E
    {set_xy, NULL, {8, 10, 11, 6}},                 // FDCB..DC SET 3,(IY+d),H
    {set_xy, NULL, {8, 10, 11, 7}},                 // FDCB..DD SET 3,(IY+d),L
    {set_xy, NULL, {8, 10, 11, -1}},                // FDCB..DE SET 3,(IY+d)
    {set_xy, NULL, {8, 10, 11, 0}},                 // FDCB..DF SET 3,(IY+d),A
    {set_xy, NULL, {16, 10, 11, 2}},                // FDCB..E0 SET 4,(IY+d),B
    {set_xy, NULL, {16, 10, 11, 3}},                // FDCB..E1 SET 4,(IY+d),C
    {set_xy, NULL, {16, 10, 11, 4}},                // FDCB..E2 SET 4,(IY+d),D
    {set_xy, NULL, {16, 10, 11, 5}},                // FDCB..E3 SET 4,(IY+d),E
    {set_xy, NULL, {16, 10, 11, 6}},                // FDCB..E4 SET 4,(IY+d),H
    {set_xy, NULL, {16, 10, 11, 7}},                // FDCB..E5 SET 4,(IY+d),L
    {set_xy, NULL, {16, 10, 11, -1}},               // FDCB..E6 SET 4,(IY+d)
    {set_xy, NULL, {16, 10, 11, 0}},                // FDCB..E7 SET 4,(IY+d),A
    {set_xy, NULL, {32, 10, 11, 2}},                // FDCB..E8 SET 5,(IY+d),B
    {set_xy, NULL, {32, 10, 11, 3}},                // FDCB..E9 SET 5,(IY+d),C
    {set_xy, NULL, {32, 10, 11, 4}},                // FDCB..EA SET 5,(IY+d),D
    {set_xy, NULL, {32, 10, 11, 5}},                // FDCB..EB SET 5,(IY+d),E
    {set_xy, NULL, {32, 10, 11, 6}},                // FDCB..EC SET 5,(IY+d),H
    {set_xy, NULL, {32, 10, 11, 7}},                // FDCB..ED SET 5,(IY+d),L
    {set_xy, NULL, {32, 10, 11, -1}},               // FDCB..EE SET 5,(IY+d)
    {set_xy, NULL, {32, 10, 11, 0}},                // FDCB..EF SET 5,(IY+d),A
    {set_xy, NULL, {64, 10, 11, 2}},                // FDCB..F0 SET 6,(IY+d),B
    {set_xy, NULL, {64, 10, 11, 3}},                // FDCB..F1 SET 6,(IY+d),C
    {set_xy, NULL, {64, 10, 11, 4}},                // FDCB..F2 SET 6,(IY+d),D
    {set_xy, NULL, {64, 10, 11, 5}},                // FDCB..F3 SET 6,(IY+d),E
    {set_xy, NULL, {64, 10, 11, 6}},                // FDCB..F4 SET 6,(IY+d),H
    {set_xy, NULL, {64, 10, 11, 7}},                // FDCB..F5 SET 6,(IY+d),L
    {set_xy, NULL, {64, 10, 11, -1}},               // FDCB..F6 SET 6,(IY+d)
    {set_xy, NULL, {64, 10, 11, 0}},                // FDCB..F7 SET 6,(IY+d),A
    {set_xy, NULL, {128, 10, 11, 2}},               // FDCB..F8 SET 7,(IY+d),B
    {set_xy, NULL, {128, 10, 11, 3}},               // FDCB..F9 SET 7,(IY+d),C
    {set_xy, NULL, {128, 10, 11, 4}},               // FDCB..FA SET 7,(IY+d),D
    {set_xy, NULL, {128, 10, 11, 5}},               // FDCB..FB SET 7,(IY+d),E
    {set_xy, NULL, {128, 10, 11, 6}},               // FDCB..FC SET 7,(IY+d),H
    {set_xy, NULL, {128, 10, 11, 7}},               // FDCB..FD SET 7,(IY+d),L
    {set_xy, NULL, {128, 10, 11, -1}},              // FDCB..FE SET 7,(IY+d)
    {set_xy, NULL, {128, 10, 11, 0}},               // FDCB..FF SET 7,(IY+d),A
};

/*****************************************************************************/

static int CSimulator_traverse(CSimulatorObject* self, visitproc visit, void *arg) {
    Py_VISIT(self->memory_obj);
    Py_VISIT(self->registers_obj);
    Py_VISIT(self->tracer);
    Py_VISIT(self->in_a_n_tracer);
    Py_VISIT(self->in_r_c_tracer);
    Py_VISIT(self->ini_tracer);
    Py_VISIT(self->out_tracer);
    return 0;
}

static int CSimulator_clear(CSimulatorObject* self) {
    Py_CLEAR(self->memory_obj);
    Py_CLEAR(self->registers_obj);
    Py_CLEAR(self->tracer);
    Py_CLEAR(self->in_a_n_tracer);
    Py_CLEAR(self->in_r_c_tracer);
    Py_CLEAR(self->ini_tracer);
    Py_CLEAR(self->out_tracer);
    return 0;
}

static void CSimulator_dealloc(CSimulatorObject* self) {
    for (int i = 0; i < 11; i++) {
        PyBuffer_Release(&self->buffers[i]);
    }
    PyObject_GC_UnTrack(self);
    CSimulator_clear(self);
    Py_TYPE(self)->tp_free((PyObject *) self);
}

static int set_memory_buffer(PyObject* source, Py_ssize_t exp_size, Py_buffer* buffer, byte** memory, int flags) {
    if (exp_size > 0) {
        Py_ssize_t size = PyObject_Size(source);
        if (size == -1) {
            return -1;
        }
        if (size != exp_size) {
            PyErr_Format(PyExc_ValueError, "Memory bank size is %d (expected %d)", size, exp_size);
            return -1;
        }
    }
    if (PyObject_GetBuffer(source, buffer, flags) == -1) {
        return -1;
    }
    *memory = buffer->buf;
    return 0;
}

static int set_memory(CSimulatorObject* self, PyObject* source) {
    int mem_ok = 0;
    PyObject* roms = NULL;
    PyObject* banks = NULL;
    PyObject* o7ffd = NULL;

    Py_XSETREF(self->memory_obj, source);
    Py_ssize_t mem_size = PyObject_Size(source);

    if (mem_size == 65536) {
        mem_ok = set_memory_buffer(source, 0, &self->buffers[0], &self->memory, PyBUF_WRITABLE);
#ifdef CONTENTION
        self->t0 = 14335 - 23;
        self->t1 = 14335 + 224 * 191 + 126;
        self->contend = contend_48k;
#endif
    } else if (mem_size == 131072) {
        roms = PyObject_GetAttrString(source, "roms");
        if (roms == NULL) {
            mem_ok = -1;
            goto done;
        }
        if (PyTuple_Check(roms) && PyTuple_Size(roms) == 2) {
            for (int i = 0; i < 2; i++) {
                PyObject* rom = PyTuple_GetItem(roms, i);
                mem_ok = set_memory_buffer(rom, 0x4000, &self->buffers[i], &self->roms[i], PyBUF_SIMPLE);
                if (mem_ok == -1) {
                    goto done;
                }
            }
        } else {
            PyErr_SetString(PyExc_TypeError, "Simulator memory.roms is not a 2-element tuple");
            mem_ok = -1;
            goto done;
        }

        banks = PyObject_GetAttrString(source, "banks");
        if (banks == NULL) {
            mem_ok = -1;
            goto done;
        }
        if (PyList_Check(banks) && PyList_Size(banks) == 8) {
            for (int i = 0; i < 8; i++) {
                PyObject* bank = PyList_GetItem(banks, i);
                mem_ok = set_memory_buffer(bank, 0x4000, &self->buffers[i + 2], &self->banks[i], PyBUF_WRITABLE);
                if (mem_ok == -1) {
                    goto done;
                }
            }
        } else {
            PyErr_SetString(PyExc_TypeError, "Simulator memory.banks is not an 8-element list");
            mem_ok = -1;
            goto done;
        }

        o7ffd = PyObject_GetAttrString(source, "o7ffd");
        if (o7ffd == NULL) {
            mem_ok = -1;
            goto done;
        }
        if (!PyLong_Check(o7ffd)) {
            PyErr_SetString(PyExc_TypeError, "memory.o7ffd is not an integer");
            mem_ok = -1;
            goto done;
        }

        self->mem128[1] = self->banks[5];
        self->mem128[2] = self->banks[2];
        out7ffd(self, PyLong_AsLong(o7ffd) & 0xFF);
#ifdef CONTENTION
        self->t0 = 14361 - 23;
        self->t1 = 14361 + 228 * 191 + 126;
        self->contend = contend_128k;
#endif
    } else {
        PyErr_SetString(PyExc_TypeError, "Simulator memory length is neither 65536 nor 131072");
        mem_ok = -1;
        goto done;
    }

done:
    Py_XDECREF(roms);
    Py_XDECREF(banks);
    Py_XDECREF(o7ffd);
    return mem_ok;
}

static int configure_registers(CSimulatorObject* self, PyObject* registers, PyObject* state) {
    int rv = -1;
    PyObject* simutils = NULL;
    PyObject* get_registers = NULL;

    simutils = PyImport_ImportModule("skoolkit.simutils");
    if (simutils == NULL) {
        goto done;
    }
    get_registers = PyObject_GetAttrString(simutils, "get_registers");
    if (get_registers == NULL) {
        goto done;
    }
    PyObject* array = PyObject_CallFunction(get_registers, "(OO)", registers, state);
    if (array == NULL) {
        goto done;
    }
    Py_XSETREF(self->registers_obj, array);
    if (PyObject_GetBuffer(array, &self->buffers[10], PyBUF_WRITABLE | PyBUF_FORMAT) == 0) {
        rv = 0;
        self->registers = self->buffers[10].buf;
    }

done:
    Py_XDECREF(simutils);
    Py_XDECREF(get_registers);
    return rv;
}

static int configure(CSimulatorObject* self, PyObject* config) {
    self->frame_duration = 69888;
    self->int_active = 32;

    PyObject *key, *value;
    Py_ssize_t pos;

    if (config && config != Py_None) {
        if (!PyDict_Check(config)) {
            PyErr_SetString(PyExc_TypeError, "'config' must be a dict");
            return -1;
        }
        pos = 0;
        while (PyDict_Next(config, &pos, &key, &value)) {
            if (!PyUnicode_Check(key)) {
                PyErr_SetString(PyExc_TypeError, "keys of 'config' must be strings");
                return -1;
            }
            if (PyUnicode_CompareWithASCIIString(key, "frame_duration") == 0) {
                if (!PyLong_Check(value)) {
                    PyErr_SetString(PyExc_TypeError, "value of 'frame_duration' must be an integer");
                    return -1;
                }
                self->frame_duration = PyLong_AsLong(value);
            } else if (PyUnicode_CompareWithASCIIString(key, "int_active") == 0) {
                if (!PyLong_Check(value)) {
                    PyErr_SetString(PyExc_TypeError, "value of 'int_active' must be an integer");
                    return -1;
                }
                self->int_active = PyLong_AsLong(value);
            }
        }
    }

    return 0;
}

static PyObject* convert_memory(PyObject* source) {
    PyObject* memory = NULL;
    char* mem = NULL;

    PyObject* mem_iter = PyObject_GetIter(source);
    if (mem_iter == NULL) {
        PyErr_SetString(PyExc_TypeError, "Failed to create iterator for memory");
        goto done;
    }

    PyObject* item;
    unsigned addr = 0;
    unsigned size = 0x10000;
    int mem_ok = 0;
    mem = malloc(size * sizeof(char));
    if (mem == NULL) {
        PyErr_SetString(PyExc_MemoryError, "Failed to allocate memory for memory object");
        goto done;
    }
    while (mem_ok == 0 && addr < size && (item = PyIter_Next(mem_iter)) != NULL) {
        if (PyLong_Check(item)) {
            mem[addr] = PyLong_AsLong(item) & 0xFF;
        } else {
            PyErr_Format(PyExc_TypeError, "Object at memory address %u is not an integer", addr);
            mem_ok = -1;
        }
        Py_DECREF(item);
        addr += 1;
    }
    Py_DECREF(mem_iter);
    if (mem_ok == -1) {
        goto done;
    }

    memory = PyByteArray_FromStringAndSize(mem, size);

done:
    if (mem) free(mem);
    return memory;
}

static int CSimulator_init(CSimulatorObject* self, PyObject* args, PyObject* kwds) {
    static char* kwlist[] = {"memory", "registers", "state", "config", NULL};
    PyObject* memory = NULL;
    PyObject* registers = Py_None;
    PyObject* state = Py_None;
    PyObject* config = NULL;
    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O|OOO", kwlist, &memory, &registers, &state, &config)) {
       return -1;
    }

    if (PyObject_Size(memory) == 0x10000) {
        memory = convert_memory(memory);
        if (memory == NULL) {
            return -1;
        }
    } else {
        PyObject* convert = PyObject_CallMethod(memory, "convert", NULL);
        if (convert == NULL) {
            return -1;
        }
        Py_DECREF(convert);
        Py_INCREF(memory);
    }
    if (set_memory(self, memory) == -1) {
        return -1;
    }

    if (configure_registers(self, registers, state) == -1) {
        return -1;
    }

    if (configure(self, config) == -1) {
        return -1;
    }

    return 0;
}

static PyObject* CSimulator_set_tracer(CSimulatorObject* self, PyObject* args, PyObject* kwds) {
    int ok = 1;
    PyObject* functools = NULL;
    PyObject* partial = NULL;
    static char* kwlist[] = {"", "in_r_c", "ini", NULL};
    PyObject* tracer = NULL;
    int in_r_c = 1;
    int ini = 1;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O|ii", kwlist, &tracer, &in_r_c, &ini)) {
        return NULL;
    }

    functools = PyImport_ImportModule("functools");
    if (functools == NULL) {
        ok = 0;
        goto done;
    }
    partial = PyObject_GetAttrString(functools, "partial");
    if (partial == NULL) {
        ok = 0;
        goto done;
    }

    Py_INCREF(tracer);
    Py_XSETREF(self->tracer, tracer);
    Py_CLEAR(self->in_a_n_tracer);
    Py_CLEAR(self->in_r_c_tracer);
    Py_CLEAR(self->ini_tracer);
    Py_CLEAR(self->out_tracer);

    if (PyObject_HasAttrString(tracer, "read_port")) {
        PyObject* read_port = PyObject_GetAttrString(tracer, "read_port");
        PyObject* args = Py_BuildValue("(OO)", read_port, self->registers_obj);
        self->in_a_n_tracer = PyObject_CallObject(partial, args);
        if (in_r_c) {
            self->in_r_c_tracer = PyObject_CallObject(partial, args);
        }
        if (ini) {
            self->ini_tracer = PyObject_CallObject(partial, args);
        }
        Py_XDECREF(args);
        Py_XDECREF(read_port);
        if (self->in_a_n_tracer == NULL) {
            ok = 0;
            goto done;
        }
        if (in_r_c && self->in_r_c_tracer == NULL) {
            ok = 0;
            goto done;
        }
        if (ini && self->ini_tracer == NULL) {
            ok = 0;
            goto done;
        }
    }

    if (PyObject_HasAttrString(tracer, "write_port")) {
        PyObject* write_port = PyObject_GetAttrString(tracer, "write_port");
        PyObject* args = Py_BuildValue("(OO)", write_port, self->registers_obj);
        self->out_tracer = PyObject_CallObject(partial, args);
        Py_XDECREF(args);
        Py_XDECREF(write_port);
        if (self->out_tracer == NULL) {
            ok = 0;
            goto done;
        }
    }

done:
    Py_XDECREF(functools);
    Py_XDECREF(partial);
    if (ok) {
        Py_RETURN_NONE;
    }
    return NULL;
}

static PyObject* CSimulator_run(CSimulatorObject* self, PyObject* args, PyObject* kwds) {
    static char* kwlist[] = {"start", "stop", "interrupts", NULL};
    unsigned start = 0x10000;
    unsigned stop = 0x10000;
    int interrupts = 0;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|IIp", kwlist, &start, &stop, &interrupts)) {
        return NULL;
    }

    unsigned long long* reg = self->registers;
    byte* mem = self->memory;
    unsigned frame_duration = self->frame_duration;
    unsigned int_active = self->int_active;

    if (start < 0x10000) {
        REG(PC) = start;
    }

    while (1) {
        unsigned pc = REG(PC);
        byte opcode = MEMGET(pc);
        OpcodeFunction* opcode_func = &opcodes[opcode];
        if (!opcode_func->func) {
            byte opcode2 = MEMGET((pc + 1) % 65536);
            switch (opcode) {
                case 0xCB:
                    opcode_func = &after_CB[opcode2];
                    break;
                case 0xED:
                    opcode_func = &after_ED[opcode2];
                    break;
                case 0xDD:
                    if (opcode2 == 0xCB) {
                        opcode_func = &after_DDCB[MEMGET((pc + 3) % 65536)];
                    } else {
                        opcode_func = &after_DD[opcode2];
                    }
                    break;
                case 0xFD:
                    if (opcode2 == 0xCB) {
                        opcode_func = &after_FDCB[MEMGET((pc + 3) % 65536)];
                    } else {
                        opcode_func = &after_FD[opcode2];
                    }
                    break;
                default:
                    break;
            }
        }

        opcode_func->func(self, opcode_func->lookup, opcode_func->args);
        if (PyErr_Occurred()) {
            return NULL;
        }

        if (interrupts && REG(IFF) && (REG(T) % frame_duration) < int_active) {
            accept_interrupt(self, pc);
        }

        if (stop > 0xFFFF || REG(PC) == stop) {
            break;
        }
    }

    Py_RETURN_NONE;
}

static PyObject* CSimulator_exec_with_cb(CSimulatorObject* self, PyObject* args, PyObject* kwds) {
    static char* kwlist[] = {"stop", "rst16_cb", NULL};
    unsigned stop;
    PyObject* rst16_cb;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "IO", kwlist, &stop, &rst16_cb)) {
        return NULL;
    }

    unsigned long long* reg = self->registers;
    byte* mem = self->memory;

    while (1) {
        byte opcode = MEMGET(REG(PC));
        OpcodeFunction* opcode_func = &opcodes[opcode];
        if (!opcode_func->func) {
            byte opcode2 = MEMGET((REG(PC) + 1) % 65536);
            switch (opcode) {
                case 0xCB:
                    opcode_func = &after_CB[opcode2];
                    break;
                case 0xED:
                    opcode_func = &after_ED[opcode2];
                    break;
                case 0xDD:
                    if (opcode2 == 0xCB) {
                        opcode_func = &after_DDCB[MEMGET((REG(PC) + 3) % 65536)];
                    } else {
                        opcode_func = &after_DD[opcode2];
                    }
                    break;
                case 0xFD:
                    if (opcode2 == 0xCB) {
                        opcode_func = &after_FDCB[MEMGET((REG(PC) + 3) % 65536)];
                    } else {
                        opcode_func = &after_FD[opcode2];
                    }
                    break;
                default:
                    break;
            }
        }

        opcode_func->func(self, opcode_func->lookup, opcode_func->args);
        if (PyErr_Occurred()) {
            return NULL;
        }

        if (opcode == 0xD7) {
            PyObject* args = Py_BuildValue("(b)", REG(A));
            PyObject* rv = PyObject_CallObject(rst16_cb, args);
            Py_XDECREF(args);
            if (rv == NULL) {
                return NULL;
            }
            Py_DECREF(rv);
        }

        if (REG(PC) == stop) {
            break;
        }
    }

    Py_RETURN_NONE;
}

static PyObject* CSimulator_exec_frame(CSimulatorObject* self, PyObject* args, PyObject* kwds) {
    static char* kwlist[] = {"fetch_count", "exec_map", "trace", NULL};
    int fetch_count;
    PyObject* exec_map = Py_None;
    PyObject* trace = Py_None;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "i|OO", kwlist, &fetch_count, &exec_map, &trace)) {
        return NULL;
    }

    unsigned long long* reg = self->registers;
    byte* mem = self->memory;
    unsigned pc;

    while (1) {
        pc = REG(PC);
        byte opcode = MEMGET(pc);
        byte opcode2 = MEMGET((pc + 1) % 65536);
        OpcodeFunction* opcode_func = &opcodes[opcode];
        unsigned r0 = REG(R);
        if (!opcode_func->func) {
            switch (opcode) {
                case 0xCB: {
                    opcode_func = &after_CB[opcode2];
                    break;
                }
                case 0xED: {
                    opcode_func = &after_ED[opcode2];
                    break;
                }
                case 0xDD: {
                    if (opcode2 == 0xCB) {
                        opcode_func = &after_DDCB[MEMGET((REG(PC) + 3) % 65536)];
                    } else {
                        opcode_func = &after_DD[opcode2];
                    }
                    break;
                }
                case 0xFD: {
                    if (opcode2 == 0xCB) {
                        opcode_func = &after_FDCB[MEMGET((REG(PC) + 3) % 65536)];
                    } else {
                        opcode_func = &after_FD[opcode2];
                    }
                    break;
                }
                default:
                    break;
            }
        }

        if (trace != Py_None) {
            PyObject* m_args = Py_BuildValue("(II)", fetch_count, pc);
            PyObject* rv = PyObject_Call(trace, m_args, NULL);
            Py_XDECREF(m_args);
            if (rv == NULL) {
                return NULL;
            }
            Py_DECREF(rv);
        }

        opcode_func->func(self, opcode_func->lookup, opcode_func->args);
        if (PyErr_Occurred()) {
            return NULL;
        }

        if (exec_map != Py_None) {
            PyObject* addr = PyLong_FromLong(pc);
            int rv = PySet_Add(exec_map, addr);
            Py_XDECREF(addr);
            if (rv == -1) {
                return NULL;
            }
        }

        if (opcode == 0xED && opcode2 == 0x4F) {
            fetch_count -= 2;
        } else {
            fetch_count -= 2 - ((REG(R) ^ r0) & 1);
        }
        if (fetch_count <= 0) {
            break;
        }
    }

    return PyLong_FromLong(pc);
}

static PyObject* CSimulator_accept_interrupt(CSimulatorObject* self, PyObject* args, PyObject* kwds) {
    static char* kwlist[] = {"", "", "", NULL};
    PyObject* registers = NULL;
    PyObject* memory = NULL;
    unsigned prev_pc = 0;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "OOi", kwlist, &registers, &memory, &prev_pc)) {
        return NULL;
    }

    if (accept_interrupt(self, prev_pc)) {
        Py_RETURN_TRUE;
    }
    Py_RETURN_FALSE;
}

static PyObject* CSimulator_trace(CSimulatorObject* self, PyObject* args, PyObject* kwds) {
    static char* kwlist[] = {"", "", "", "", "", "", "", NULL};
    PyObject* start_obj;
    PyObject* stop_obj;
    unsigned long long max_operations;
    unsigned long long max_time;
    int interrupts;
    PyObject* disassemble;
    PyObject* trace;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "OOKKiOO", kwlist, &start_obj, &stop_obj, &max_operations, &max_time, &interrupts, &disassemble, &trace)) {
        return NULL;
    }

    unsigned start = PyLong_Check(start_obj) ? PyLong_AsLong(start_obj) : 0x10000;
    unsigned stop = PyLong_Check(stop_obj) ? PyLong_AsLong(stop_obj) : 0x10000;
    unsigned long long* reg = self->registers;
    byte* mem = self->memory;
    unsigned frame_duration = self->frame_duration;
    unsigned int_active = self->int_active;
    unsigned long long operations = 0;
    if (start < 0x10000) {
        REG(PC) = start;
    }

    while (1) {
        PyObject* i = NULL;
        unsigned long long t0 = REG(T);
        unsigned pc = REG(PC);
        byte opcode = MEMGET(pc);
        OpcodeFunction* opcode_func = &opcodes[opcode];
        if (!opcode_func->func) {
            byte opcode2 = MEMGET((pc + 1) % 65536);
            switch (opcode) {
                case 0xCB:
                    opcode_func = &after_CB[opcode2];
                    break;
                case 0xED:
                    opcode_func = &after_ED[opcode2];
                    break;
                case 0xDD:
                    if (opcode2 == 0xCB) {
                        opcode_func = &after_DDCB[MEMGET((pc + 3) % 65536)];
                    } else {
                        opcode_func = &after_DD[opcode2];
                    }
                    break;
                case 0xFD:
                    if (opcode2 == 0xCB) {
                        opcode_func = &after_FDCB[MEMGET((pc + 3) % 65536)];
                    } else {
                        opcode_func = &after_FD[opcode2];
                    }
                    break;
                default:
                    break;
            }
        }

        if (disassemble != Py_None) {
            PyObject* args = Py_BuildValue("(I)", pc);
            i = PyObject_CallObject(disassemble, args);
            Py_XDECREF(args);
            if (i == NULL) {
                return NULL;
            }
        }

        opcode_func->func(self, opcode_func->lookup, opcode_func->args);
        if (PyErr_Occurred()) {
            return NULL;
        }

        if (trace != Py_None) {
            PyObject* args = Py_BuildValue("(INK)", pc, i, t0);
            PyObject* rv = PyObject_CallObject(trace, args);
            Py_XDECREF(args);
            if (rv == NULL) {
                return NULL;
            }
            Py_DECREF(rv);
        }

        if (interrupts && REG(IFF) && (REG(T) % frame_duration) < int_active) {
            accept_interrupt(self, pc);
        }

        operations += 1;

        if (max_operations > 0 && operations >= max_operations) {
            return Py_BuildValue("(IL)", 1, operations);
        }
        if (max_time > 0 && REG(T) >= max_time) {
            return Py_BuildValue("(IL)", 2, operations);
        }
        if (REG(PC) == stop) {
            return Py_BuildValue("(IL)", 3, operations);
        }
    }

    Py_RETURN_NONE;
}

static PyObject* CSimulator_press_keys(CSimulatorObject* self, PyObject* args, PyObject* kwds) {
    static char* kwlist[] = {"", "", "", "", "", NULL};
    PyObject* keys;
    unsigned stop;
    unsigned timeout;
    PyObject* disassemble;
    PyObject* trace;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "OIIOO", kwlist, &keys, &stop, &timeout, &disassemble, &trace)) {
        return NULL;
    }

    PyObject* pop = PyObject_GetAttrString(keys, "pop");
    if (pop == NULL) {
        return NULL;
    }

    unsigned long long* reg = self->registers;
    byte* mem = self->memory;
    unsigned frame_duration = self->frame_duration;
    unsigned int_active = self->int_active;

    while (1) {
        PyObject* i = NULL;
        unsigned pc = REG(PC);
        unsigned long long t0 = REG(T);
        byte opcode = MEMGET(pc);
        OpcodeFunction* opcode_func = &opcodes[opcode];
        if (!opcode_func->func) {
            byte opcode2 = MEMGET((pc + 1) % 65536);
            switch (opcode) {
                case 0xCB:
                    opcode_func = &after_CB[opcode2];
                    break;
                case 0xED:
                    opcode_func = &after_ED[opcode2];
                    break;
                case 0xDD:
                    if (opcode2 == 0xCB) {
                        opcode_func = &after_DDCB[MEMGET((pc + 3) % 65536)];
                    } else {
                        opcode_func = &after_DD[opcode2];
                    }
                    break;
                case 0xFD:
                    if (opcode2 == 0xCB) {
                        opcode_func = &after_FDCB[MEMGET((pc + 3) % 65536)];
                    } else {
                        opcode_func = &after_FD[opcode2];
                    }
                    break;
                default:
                    break;
            }
        }

        if (disassemble != Py_None) {
            PyObject* args = Py_BuildValue("(I)", pc);
            i = PyObject_CallObject(disassemble, args);
            Py_XDECREF(args);
            if (i == NULL) {
                return NULL;
            }
        }

        opcode_func->func(self, opcode_func->lookup, opcode_func->args);
        if (PyErr_Occurred()) {
            return NULL;
        }

        if (trace != Py_None) {
            PyObject* args = Py_BuildValue("(INK)", pc, i, t0);
            PyObject* t = PyObject_CallObject(trace, args);
            Py_XDECREF(args);
            if (t == NULL) {
                return NULL;
            }
            Py_DECREF(t);
        }

        if (REG(IFF) && (REG(T) % frame_duration) < int_active) {
            if (accept_interrupt(self, pc) && PyList_Size(keys)) {
                PyObject* k = PyList_GetItem(keys, 0);
                if (k == NULL) {
                    return NULL;
                }
                if (!PyObject_IsTrue(k)) {
                    PyObject* args = Py_BuildValue("(I)", 0);
                    PyObject* p = PyObject_CallObject(pop, args);
                    Py_XDECREF(args);
                    if (p == NULL) {
                        return NULL;
                    }
                    Py_DECREF(p);
                }
            }
        }

        if (REG(PC) == stop || REG(T) > timeout) {
            break;
        }
    }

    Py_RETURN_NONE;
}

static int advance_tape(PyObject* tracer, unsigned* tracer_state, unsigned* edges, unsigned max_index, unsigned long long tstates, PyObject* print_progress, unsigned* progress) {
    unsigned tape_running = tracer_state[4];
    if (!tape_running) {
        return 0;
    }

    unsigned next_edge = tracer_state[0];
    if (tstates < next_edge) {
        return 0;
    }

    unsigned index = tracer_state[1];
    while (index < max_index) {
        unsigned edge = edges[index + 1];
        if (edge >= tstates) {
            break;
        }
        index += 1;
    }
    tracer_state[1] = index;

    unsigned block_max_index = tracer_state[3];
    unsigned edge = edges[index];
    if (index == max_index) {
        /* Allow 1ms for the final edge on the tape to be read */
        if (tstates - edge > 3500) {
            PyObject* rv = PyObject_CallMethod(tracer, "stop_tape", "(K)", tstates);
            if (rv == NULL) {
                return -1;
            }
            Py_DECREF(rv);
        }
    } else if (index > block_max_index) {
        /* Pause tape between blocks */
        PyObject* rv = PyObject_CallMethod(tracer, "next_block", "(K)", tstates);
        if (rv == NULL) {
            return -1;
        }
        Py_DECREF(rv);
    } else {
        tracer_state[0] = edges[index + 1];
        if (index < block_max_index) {
            unsigned p = edge / (edges[max_index] / 1000);
            if (p > *progress) {
                PyObject* args = Py_BuildValue("(I)", p);
                PyObject* rv = PyObject_CallObject(print_progress, args);
                Py_XDECREF(args);
                if (rv == NULL) {
                    return -1;
                }
                Py_DECREF(rv);
                *progress = p;
            }
        }
    }

    return 0;
}

#ifndef CONTENTION
static void dec_a_jr(CSimulatorObject* self, void* lookup, int args[]) {
    unsigned long long* reg = self->registers;
    byte* mem = self->memory;

    byte a = REG(A);
    unsigned pc1 = (REG(PC) + 1) % 65536;
    if (REG(IFF) == 0 && a && MEMGET(pc1) == 0x20 && MEMGET((pc1 + 1) % 65536) == 0xFD) {
        REG(A) = 0;
        REG(F) = 0x42 + (REG(F) & 1);
        INC_R(a * 2);
        INC_T(16 * a - 5);
        REG(PC) = (pc1 + 2) % 65536;
    } else {
        REG(A) = DEC[REG(F) & 1][a][0];
        REG(F) = DEC[REG(F) & 1][a][1];
        INC_R(1);
        INC_T(4);
        REG(PC) = pc1;
    }
}

static void dec_a_jp(CSimulatorObject* self, void* lookup, int args[]) {
    unsigned long long* reg = self->registers;
    byte* mem = self->memory;

    byte a = REG(A);
    unsigned pc = REG(PC);
    if (REG(IFF) == 0 && a && MEMGET((pc + 1) % 65536) == 0xC2 && MEMGET((pc + 2) % 65536) == pc % 256 && MEMGET((pc + 3) % 65536) == pc / 256) {
        REG(A) = 0;
        REG(F) = 0x42 + (REG(F) & 1);
        INC_R(a * 2);
        INC_T(14 * a);
        REG(PC) = (pc + 4) % 65536;
    } else {
        REG(A) = DEC[REG(F) & 1][a][0];
        REG(F) = DEC[REG(F) & 1][a][1];
        INC_R(1);
        INC_T(4);
        REG(PC) = (pc + 1) % 65536;
    }
}

static void dec_a_list(CSimulatorObject* self, void* lookup, int args[]) {
    unsigned long long* reg = self->registers;
    byte* mem = self->memory;

    unsigned pc = REG(PC);
    if (REG(IFF) == 0) {
        if (MEMGET((pc + 1) % 65536) == 0x20 && MEMGET((pc + 2) % 65536) == 0xFD) {
            args[0]++;
            dec_a_jr(self, lookup, args);
            return;
        }
        if (MEMGET((pc + 1) % 65536) == 0xC2 && MEMGET((pc + 2) % 65536) == pc % 256 && MEMGET((pc + 3) % 65536) == pc / 256) {
            args[1]++;
            dec_a_jp(self, lookup, args);
            return;
        }
    }

    /* Increment the miss count */
    args[2]++;

    byte a = REG(A);
    REG(A) = DEC[REG(F) & 1][a][0];
    REG(F) = DEC[REG(F) & 1][a][1];
    INC_R(1);
    INC_T(4);
    REG(PC) = (pc + 1) % 65536;
}

static void dec_b(CSimulatorObject* self, void* lookup, int args[]) {
    tsl_accelerator** accs = (tsl_accelerator**)lookup;
    int num_accs = args[0];
    unsigned* state = accs[0]->state;
    unsigned long long* reg = self->registers;
    byte* mem = self->memory;

    byte b = REG(B);
    unsigned pc1 = (REG(PC) + 1) % 65536;
    if (state[4] && REG(IFF) == 0) {
        unsigned loops = 0;
        for (int k = 0; k < num_accs; k++) {
            tsl_accelerator* acc = accs[k];
            int match = 1;
            int i = 0;
            for (int j = acc->c0; j < acc->c1; j++) {
                unsigned c = acc->code[i++];
                if (c < 256 && c != MEMGET((pc1 + j) % 65536)) {
                    match = 0;
                    break;
                }
            }
            if (match) {
                if ((REG(C) & acc->ear_mask) == ((state[1] - acc->polarity) & 1) * acc->ear_mask) {
                    int delta = state[0] - REG(T) - acc->in_time;
                    if (delta > 0) {
                        unsigned d1 = delta / acc->loop_time + 1;
                        unsigned d2 = (b - 1) & 0xFF;
                        loops = d1 < d2 ? d1 : d2;
                        if (loops) {
                            /* The carry flag is cleared on each loop iteration */
                            REG(F) &= 0xFE;
                        }
                    }
                }
                if (k) {
                    /* Move the selected accelerator to the beginning of the
                       list so that it can be found quicker next time */
                    tsl_accelerator* first = accs[0];
                    accs[0] = acc;
                    accs[k] = first;
                }
                REG(B) = DEC[REG(F) & 1][(b - loops) & 0xFF][0];
                REG(F) = DEC[REG(F) & 1][(b - loops) & 0xFF][1];
                INC_R(acc->loop_r_inc * loops + 1);
                INC_T(acc->loop_time * loops + 4);
                REG(PC) = pc1;
                return;
            }
        }
    }

    REG(B) = DEC[REG(F) & 1][b][0];
    REG(F) = DEC[REG(F) & 1][b][1];
    INC_R(1);
    INC_T(4);
    REG(PC) = pc1;
}

static void inc_b(CSimulatorObject* self, void* lookup, int args[]) {
    tsl_accelerator** accs = (tsl_accelerator**)lookup;
    int num_accs = args[0];
    unsigned* state = accs[0]->state;
    unsigned long long* reg = self->registers;
    byte* mem = self->memory;

    byte b = REG(B);
    unsigned pc1 = (REG(PC) + 1) % 65536;
    if (state[4] && REG(IFF) == 0) {
        unsigned loops = 0;
        for (int k = 0; k < num_accs; k++) {
            tsl_accelerator* acc = accs[k];
            int match = 1;
            int i = 0;
            for (int j = acc->c0; j < acc->c1; j++) {
                unsigned c = acc->code[i++];
                if (c < 256 && c != MEMGET((pc1 + j) % 65536)) {
                    match = 0;
                    break;
                }
            }
            if (match) {
                if ((REG(C) & acc->ear_mask) == ((state[1] - acc->polarity) & 1) * acc->ear_mask) {
                    int delta = state[0] - REG(T) - acc->in_time;
                    if (delta > 0) {
                        unsigned d1 = delta / acc->loop_time + 1;
                        unsigned d2 = 255 - b;
                        loops = d1 < d2 ? d1 : d2;
                        if (loops) {
                            /* The carry flag is cleared on each loop iteration */
                            REG(F) &= 0xFE;
                        }
                    }
                }
                if (k) {
                    /* Move the selected accelerator to the beginning of the
                       list so that it can be found quicker next time */
                    tsl_accelerator* first = accs[0];
                    accs[0] = acc;
                    accs[k] = first;
                }
                REG(B) = INC[REG(F) & 1][b + loops][0];
                REG(F) = INC[REG(F) & 1][b + loops][1];
                INC_R(acc->loop_r_inc * loops + 1);
                INC_T(acc->loop_time * loops + 4);
                REG(PC) = pc1;
                return;
            }
        }
    }

    REG(B) = INC[REG(F) & 1][b][0];
    REG(F) = INC[REG(F) & 1][b][1];
    INC_R(1);
    INC_T(4);
    REG(PC) = pc1;
}

static void list_accelerators(CSimulatorObject* self, void* lookup, int args[]) {
    tsl_accelerator** accs = (tsl_accelerator**)lookup;
    int num_accs = args[0];
    byte opcode = args[1];
    unsigned* state = accs[0]->state;
    unsigned long long* reg = self->registers;
    byte* mem = self->memory;

    unsigned pc1 = (REG(PC) + 1) % 65536;
    if (state[4] && REG(IFF) == 0) {
        for (int k = 0; k < num_accs; k++) {
            tsl_accelerator* acc = accs[k];
            int match = 1;
            int i = 0;
            for (int j = acc->c0; j < acc->c1; j++) {
                unsigned c = acc->code[i++];
                if (c < 256 && c != MEMGET((pc1 + j) % 65536)) {
                    match = 0;
                    break;
                }
            }
            if (match) {
                acc->hits++;
                if (k) {
                    /* Move the selected accelerator to the beginning of the
                       list so that it can be found quicker by inc_b/dec_b */
                    tsl_accelerator* first = accs[0];
                    accs[0] = acc;
                    accs[k] = first;
                }
                if (opcode == 0x04) {
                    inc_b(self, lookup, args);
                } else {
                    dec_b(self, lookup, args);
                }
                return;
            }
        }
    }

    /* Increment the miss count */
    args[2]++;

    byte b = REG(B);
    if (opcode == 0x04) {
        REG(B) = INC[REG(F) & 1][b][0];
        REG(F) = INC[REG(F) & 1][b][1];
    } else {
        REG(B) = DEC[REG(F) & 1][b][0];
        REG(F) = DEC[REG(F) & 1][b][1];
    }
    INC_R(1);
    INC_T(4);
    REG(PC) = pc1;
}

static int get_tsl_accelerators(PyObject* accelerators, tsl_accelerator* accs, unsigned* tracer_state) {
    PyObject* iter = PyObject_GetIter(accelerators);
    if (iter == NULL) {
        return -1;
    }

    int ok = 1;
    PyObject* item;
    int i = 0;
    while ((item = PyIter_Next(iter)) != NULL) {
        tsl_accelerator* accelerator = &accs[i++];
        PyObject* name = PyObject_GetAttrString(item, "name");
        PyObject* opcode_obj = PyObject_GetAttrString(item, "opcode");
        PyObject* code_obj = PyObject_GetAttrString(item, "code");
        PyObject* c0_obj = PyObject_GetAttrString(item, "c0");
        PyObject* c1_obj = PyObject_GetAttrString(item, "c1");
        PyObject* in_time_obj = PyObject_GetAttrString(item, "in_time");
        PyObject* loop_time_obj = PyObject_GetAttrString(item, "loop_time");
        PyObject* loop_r_inc_obj = PyObject_GetAttrString(item, "loop_r_inc");
        PyObject* ear_mask_obj = PyObject_GetAttrString(item, "ear_mask");
        PyObject* polarity_obj = PyObject_GetAttrString(item, "polarity");
        if (name == NULL || opcode_obj == NULL || code_obj == NULL || c0_obj == NULL || c1_obj == NULL || in_time_obj == NULL ||
            loop_time_obj == NULL || loop_r_inc_obj == NULL || ear_mask_obj == NULL || polarity_obj == NULL) {
            ok = 0;
        } else {
            accelerator->name = name;
            accelerator->opcode = (byte)PyLong_AsLong(opcode_obj);
            accelerator->c0 = 0 - PyLong_AsLong(c0_obj);
            accelerator->c1 = PyLong_AsLong(c1_obj);
            accelerator->in_time = PyLong_AsLong(in_time_obj);
            accelerator->loop_time = PyLong_AsLong(loop_time_obj);
            accelerator->loop_r_inc = PyLong_AsLong(loop_r_inc_obj);
            accelerator->ear_mask = PyLong_AsLong(ear_mask_obj);
            accelerator->polarity = PyLong_AsLong(polarity_obj);
            accelerator->state = tracer_state;
            accelerator->hits = 0;
            Py_ssize_t code_len = PyList_Size(code_obj);
            accelerator->code = malloc(code_len * sizeof(unsigned));
            if (accelerator->code) {
                for (int i = 0; i < code_len; i++) {
                    PyObject* b = PyList_GetItem(code_obj, i);
                    if (b == NULL) {
                        ok = 0;
                    } else if (b == Py_None) {
                        accelerator->code[i] = 256;
                    } else {
                        accelerator->code[i] = PyLong_AsLong(b);
                    }
                }
            } else {
                ok = 0;
            }
        }
        Py_XDECREF(opcode_obj);
        Py_XDECREF(code_obj);
        Py_XDECREF(c0_obj);
        Py_XDECREF(c1_obj);
        Py_XDECREF(in_time_obj);
        Py_XDECREF(loop_time_obj);
        Py_XDECREF(loop_r_inc_obj);
        Py_XDECREF(ear_mask_obj);
        Py_XDECREF(polarity_obj);
        Py_DECREF(item);
        if (!ok) {
            break;
        }
    }
    Py_DECREF(iter);

    return ok ? i : -1;
}
#endif

static PyObject* CSimulator_load(CSimulatorObject* self, PyObject* args, PyObject* kwds) {
    static char* kwlist[] = {"", "", "", "", "", "", NULL};
    PyObject* stop_obj;
    int fast_load;
    unsigned timeout;
    PyObject* print_progress;
    PyObject* disassemble;
    PyObject* trace;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "OiIOOO", kwlist, &stop_obj, &fast_load, &timeout, &print_progress, &disassemble, &trace)) {
        return NULL;
    }

    int ok = 1;

    Py_buffer edges_buffer;
    PyObject* e = ok ? PyObject_GetAttrString(self->tracer, "edges") : NULL;
    if (e == NULL || PyObject_GetBuffer(e, &edges_buffer, PyBUF_SIMPLE) == -1) {
        ok = 0;
    }
    Py_XDECREF(e);
    unsigned* edges = edges_buffer.buf;
    unsigned max_index = edges ? (unsigned)(edges_buffer.len / edges_buffer.itemsize) - 1 : 0;

    Py_buffer ts_buffer;
    PyObject* ts = ok ? PyObject_GetAttrString(self->tracer, "state") : NULL;
    if (ts == NULL || PyObject_GetBuffer(ts, &ts_buffer, PyBUF_WRITABLE) == -1) {
        ok = 0;
    }
    Py_XDECREF(ts);
    unsigned* tracer_state = ts_buffer.buf;

    PyObject* ft = ok ? PyObject_GetAttrString(self->tracer, "finish_tape") : NULL;
    if (ft == NULL) {
        ok = 0;
    }
    int finish_tape = ft ? PyLong_AsLong(ft) : 0;
    Py_XDECREF(ft);

    PyObject* fast_load_method = ok ? PyObject_GetAttrString(self->tracer, "fast_load") : NULL;
    if (fast_load_method == NULL) {
        ok = 0;
    }

    for (int i = 0; i < 256; i++) {
        self->opcodes[i] = &opcodes[i];
    }
#ifndef CONTENTION
    OpcodeFunction dec_a_jr_accelerator = {dec_a_jr, NULL, {0}};
    OpcodeFunction dec_a_jp_accelerator = {dec_a_jp, NULL, {0}};
    OpcodeFunction dec_a_accelerator = {dec_a_list, NULL, {0}};
    if (tracer_state[6]) {
        self->opcodes[0x3D] = &dec_a_accelerator;
    } else if (tracer_state[5] == 1) {
        self->opcodes[0x3D] = &dec_a_jr_accelerator;
    } else if (tracer_state[5] == 2) {
        self->opcodes[0x3D] = &dec_a_jp_accelerator;
    }

    PyObject* accelerators = ok ? PyObject_GetAttrString(self->tracer, "accelerators") : NULL;
    if (accelerators == NULL) {
        ok = 0;
    }
    Py_ssize_t num_accs = PySet_Check(accelerators) ? PySet_Size(accelerators) : 0;
    tsl_accelerator* accs = NULL;
    tsl_accelerator** inc_b_accs = NULL;
    tsl_accelerator** dec_b_accs = NULL;
    OpcodeFunction inc_b_accelerator = {tracer_state[6] ? list_accelerators : inc_b, NULL, {0, 0x04}};
    OpcodeFunction dec_b_accelerator = {tracer_state[6] ? list_accelerators : dec_b, NULL, {0, 0x05}};
    if (ok && num_accs) {
        accs = malloc(num_accs * sizeof(tsl_accelerator));
        inc_b_accs = malloc(num_accs * sizeof(tsl_accelerator*));
        dec_b_accs = malloc(num_accs * sizeof(tsl_accelerator*));
        if (accs && inc_b_accs && dec_b_accs && get_tsl_accelerators(accelerators, accs, tracer_state) == num_accs) {
            int inc_b_ctr = 0;
            int dec_b_ctr = 0;
            for (int i = 0; i < num_accs; i++) {
                tsl_accelerator* acc = &accs[i];
                if (acc->opcode == 0x04) {
                    inc_b_accs[inc_b_ctr++] = acc;
                } else if (acc->opcode == 0x05) {
                    dec_b_accs[dec_b_ctr++] = acc;
                }
            }
            inc_b_accelerator.lookup = inc_b_accs;
            inc_b_accelerator.args[0] = inc_b_ctr;
            dec_b_accelerator.lookup = dec_b_accs;
            dec_b_accelerator.args[0] = dec_b_ctr;
            if (inc_b_ctr) {
                self->opcodes[0x04] = &inc_b_accelerator;
            }
            if (dec_b_ctr) {
                self->opcodes[0x05] = &dec_b_accelerator;
            }
        } else {
            ok = 0;
        }
    }
#endif

    unsigned long long* reg = self->registers;
    byte* mem = self->memory;
    if (mem) {
        self->out7ffd = 0x10; // Signal: 48K ROM always
    }
    unsigned frame_duration = self->frame_duration;
    unsigned int_active = self->int_active;
    unsigned progress = 0;
    unsigned pc = REG(PC);
    unsigned stop = stop_obj == Py_None ? 0x10000 : PyLong_AsLong(stop_obj);
    PyObject* rv = NULL;

    while (ok) {
        PyObject* i = NULL;
        unsigned long long t0 = REG(T);
        byte opcode = MEMGET(pc);
        OpcodeFunction* opcode_func = self->opcodes[opcode];
        if (!opcode_func->func) {
            byte opcode2 = MEMGET((pc + 1) % 65536);
            switch (opcode) {
                case 0xCB:
                    opcode_func = &after_CB[opcode2];
                    break;
                case 0xED:
                    opcode_func = &after_ED[opcode2];
                    break;
                case 0xDD:
                    if (opcode2 == 0xCB) {
                        opcode_func = &after_DDCB[MEMGET((pc + 3) % 65536)];
                    } else {
                        opcode_func = &after_DD[opcode2];
                    }
                    break;
                case 0xFD:
                    if (opcode2 == 0xCB) {
                        opcode_func = &after_FDCB[MEMGET((pc + 3) % 65536)];
                    } else {
                        opcode_func = &after_FD[opcode2];
                    }
                    break;
                default:
                    break;
            }
        }

        if (disassemble != Py_None) {
            PyObject* args = Py_BuildValue("(I)", pc);
            i = PyObject_CallObject(disassemble, args);
            Py_XDECREF(args);
            if (i == NULL) {
                break;
            }
        }

        opcode_func->func(self, opcode_func->lookup, opcode_func->args);
        if (PyErr_Occurred()) {
            break;
        }

        if (trace != Py_None) {
            PyObject* args = Py_BuildValue("(INK)", pc, i, t0);
            PyObject* t = PyObject_CallObject(trace, args);
            Py_XDECREF(args);
            if (t == NULL) {
                break;
            }
            Py_DECREF(t);
        }

        if (REG(IFF) && (REG(T) % frame_duration) < int_active) {
            accept_interrupt(self, pc);
        }

        unsigned long long tstates = REG(T);
        if (advance_tape(self->tracer, tracer_state, edges, max_index, tstates, print_progress, &progress) == -1) {
            break;
        }

        pc = REG(PC);
        unsigned end_of_tape = tracer_state[2];
        if (pc == stop && (end_of_tape || !finish_tape)) {
            rv = PyLong_FromLong(0);
            break;
        }

        int did_fast_load = 0;
        if (pc == 0x0556 && self->out7ffd & 0x10 && fast_load) {
            PyObject* args = Py_BuildValue("(O)", self);
            PyObject* fl = PyObject_CallObject(fast_load_method, args);
            Py_XDECREF(args);
            if (fl == NULL) {
                break;
            }
            did_fast_load = PyObject_IsTrue(fl);
            Py_DECREF(fl);
            if (did_fast_load) {
                unsigned block_max_index = tracer_state[3];
                tracer_state[1] = block_max_index;
                if (block_max_index == max_index) {
                    /* Final block, so stop the tape */
                    PyObject* st = PyObject_CallMethod(self->tracer, "stop_tape", "(K)", tstates);
                    if (st == NULL) {
                        break;
                    }
                    Py_DECREF(st);
                } else {
                    /* Otherwise continue to play the tape until this block's
                       'pause' period (if any) has elapsed */
                    tracer_state[4] = 1;
                    tracer_state[0] = edges[block_max_index];
                    REG(T) = edges[block_max_index];
                }
            }
            pc = REG(PC);
        }
        if (!did_fast_load) {
            if (end_of_tape && stop == 0x10000) {
                PyObject* cl = PyObject_GetAttrString(self->tracer, "custom_loader");
                if (cl == NULL) {
                    break;
                }
                int custom_loader = PyObject_IsTrue(cl);
                Py_DECREF(cl);
                if (custom_loader) {
                    rv = PyLong_FromLong(1);
                    break;
                }
                if (pc > 0x3FFF) {
                    rv = PyLong_FromLong(2);
                    break;
                }
                PyObject* tet = PyObject_GetAttrString(self->tracer, "tape_end_time");
                if (tet == NULL) {
                    break;
                }
                unsigned tape_end_time = PyLong_AsLong(tet);
                Py_DECREF(tet);
                if (REG(T) - tape_end_time > 3500000) {
                    rv = PyLong_FromLong(3);
                    break;
                }
            }
            if (REG(T) > timeout) {
                rv = PyLong_FromLong(4);
                break;
            }
        }
    }

#ifndef CONTENTION
    if (rv && tracer_state[6] && accs) {
        PyObject* acc_usage = PyObject_GetAttrString(self->tracer, "acc_usage");
        ok = acc_usage != NULL;
        if (ok) {
            for (int i = 0; i < num_accs; i++) {
                tsl_accelerator* acc = &accs[i];
                if (acc && acc->hits) {
                    PyObject* hits = PyLong_FromLong(acc->hits);
                    ok = hits && PyDict_SetItem(acc_usage, acc->name, hits) == 0;
                    Py_XDECREF(hits);
                    if (!ok) {
                        break;
                    }
                }
            }
            Py_DECREF(acc_usage);
        }
        PyObject* dec_a_jr_hits = PyLong_FromLong(dec_a_accelerator.args[0]);
        PyObject* dec_a_jp_hits = PyLong_FromLong(dec_a_accelerator.args[1]);
        PyObject* dec_a_misses = PyLong_FromLong(dec_a_accelerator.args[2]);
        PyObject* inc_b_misses = PyLong_FromLong(inc_b_accelerator.args[2]);
        PyObject* dec_b_misses = PyLong_FromLong(dec_b_accelerator.args[2]);
        if (PyObject_SetAttrString(self->tracer, "dec_a_jr_hits", dec_a_jr_hits) == -1 ||
            PyObject_SetAttrString(self->tracer, "dec_a_jp_hits", dec_a_jp_hits) == -1 ||
            PyObject_SetAttrString(self->tracer, "dec_a_misses", dec_a_misses) == -1 ||
            PyObject_SetAttrString(self->tracer, "inc_b_misses", inc_b_misses) == -1 ||
            PyObject_SetAttrString(self->tracer, "dec_b_misses", dec_b_misses) == -1) {
            ok = 0;
        }
        Py_XDECREF(dec_a_jr_hits);
        Py_XDECREF(dec_a_jp_hits);
        Py_XDECREF(dec_a_misses);
        Py_XDECREF(inc_b_misses);
        Py_XDECREF(dec_b_misses);
    }
    if (accs) {
        for (int i = 0; i < num_accs; i++) {
            tsl_accelerator* acc = &accs[i];
            if (acc) {
                Py_XDECREF(acc->name);
                if (acc->code) free(acc->code);
            }
        }
        free(accs);
    }
    if (inc_b_accs) free(inc_b_accs);
    if (dec_b_accs) free(dec_b_accs);
    Py_XDECREF(accelerators);
#endif
    if (edges) PyBuffer_Release(&edges_buffer);
    if (tracer_state) PyBuffer_Release(&ts_buffer);
    Py_XDECREF(fast_load_method);
    if (!ok) {
        Py_XDECREF(rv);
        rv = NULL;
    }
    return rv;
}

static PyMemberDef CSimulator_members[] = {
    {"memory", T_OBJECT_EX, offsetof(CSimulatorObject, memory_obj), 0, "memory"},
    {"registers", T_OBJECT_EX, offsetof(CSimulatorObject, registers_obj), 0, "registers"},
    {"tracer", T_OBJECT_EX, offsetof(CSimulatorObject, tracer), 0, "tracer"},
    {NULL}  /* Sentinel */
};

static PyMethodDef CSimulator_methods[] = {
    {"accept_interrupt", (PyCFunction) CSimulator_accept_interrupt, METH_VARARGS | METH_KEYWORDS, "Accept an interrupt if allowed"},
    {"exec_frame", (PyCFunction) CSimulator_exec_frame, METH_VARARGS | METH_KEYWORDS, "Execute an RZX frame"},
    {"exec_with_cb", (PyCFunction) CSimulator_exec_with_cb, METH_VARARGS | METH_KEYWORDS, "Execute one or more instructions with an 'RST $10' callback"},
    {"load", (PyCFunction) CSimulator_load, METH_VARARGS | METH_KEYWORDS, "Load a tape"},
    {"press_keys", (PyCFunction) CSimulator_press_keys, METH_VARARGS | METH_KEYWORDS, "Simulate keypresses"},
    {"run", (PyCFunction) CSimulator_run, METH_VARARGS | METH_KEYWORDS, "Execute one or more instructions"},
    {"set_tracer", (PyCFunction) CSimulator_set_tracer, METH_VARARGS | METH_KEYWORDS, "Set the tracer"},
    {"trace", (PyCFunction) CSimulator_trace, METH_VARARGS | METH_KEYWORDS, "Execute one or more instructions with optional tracing"},
    {NULL}  /* Sentinel */
};

static PyTypeObject CSimulatorType = {
    PyVarObject_HEAD_INIT(NULL, 0)
#ifdef CONTENTION
    .tp_name = "ccmiosimulator.CCMIOSimulator",
    .tp_doc = PyDoc_STR("CCMIOSimulator objects"),
#else
    .tp_name = "csimulator.CSimulator",
    .tp_doc = PyDoc_STR("CSimulator objects"),
#endif
    .tp_basicsize = sizeof(CSimulatorObject),
    .tp_itemsize = 0,
    .tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE | Py_TPFLAGS_HAVE_GC,
    .tp_new = PyType_GenericNew,
    .tp_free = PyObject_GC_Del,
    .tp_init = (initproc) CSimulator_init,
    .tp_dealloc = (destructor) CSimulator_dealloc,
    .tp_traverse = (traverseproc) CSimulator_traverse,
    .tp_clear = (inquiry) CSimulator_clear,
    .tp_members = CSimulator_members,
    .tp_methods = CSimulator_methods,
};

static PyModuleDef csimulatormodule = {
    PyModuleDef_HEAD_INIT,
#ifdef CONTENTION
    .m_name = "ccmiosimulator",
    .m_doc = "CCMIOSimulator wrapper class for Simulator.",
#else
    .m_name = "csimulator",
    .m_doc = "CSimulator wrapper class for Simulator.",
#endif
    .m_size = -1,
};

#ifdef CONTENTION
PyMODINIT_FUNC PyInit_ccmiosimulator(void) {
#else
PyMODINIT_FUNC PyInit_csimulator(void) {
#endif
    PyObject* m;
    if (PyType_Ready(&CSimulatorType) < 0) {
        return NULL;
    }

    m = PyModule_Create(&csimulatormodule);
    if (m == NULL) {
        return NULL;
    }

    Py_INCREF(&CSimulatorType);
#ifdef CONTENTION
    if (PyModule_AddObject(m, "CCMIOSimulator", (PyObject *) &CSimulatorType) < 0) {
#else
    if (PyModule_AddObject(m, "CSimulator", (PyObject *) &CSimulatorType) < 0) {
#endif
        Py_DECREF(&CSimulatorType);
        Py_DECREF(m);
        return NULL;
    }

    init_lookup_tables();

    return m;
}
