from enum import Enum
from typing import NamedTuple, Union, Iterator, Sequence, Optional, Mapping, Tuple

from BitVector import BitVector

from rep.instr_pretty_print import familystr


class Register(Enum):
    """An enumeration of the 32 unprivileged RISC-V integer registers."""

    ZERO = 0
    RA = 1
    SP = 2
    GP = 3
    TP = 4
    T0 = 5
    T1 = 6
    T2 = 7
    S0 = 8
    S1 = 9
    A0 = 10
    A1 = 11
    A2 = 12
    A3 = 13
    A4 = 14
    A5 = 15
    A6 = 16
    A7 = 17
    S2 = 18
    S3 = 19
    S4 = 20
    S5 = 21
    S6 = 22
    S7 = 23
    S8 = 24
    S9 = 25
    S10 = 26
    S11 = 27
    T3 = 28
    T4 = 29
    T5 = 30
    T6 = 31


imm_sizes: Mapping[str, int] = {
    "i": 12,
    "s": 12,
    "b": 12,
    "bz": 12,
    "u": 20,
    "j": 20,
    "li": 32
}
"""Dictionary of immediate formats with associated immediate field size."""


class Statement:
    """An assembler source statement."""

    labels: Sequence[str]

    def __init__(self, labels: Optional[Sequence[str]] = None):
        """
        Instantiates a new assembler source statement.

        :param labels: an optional set of labels to mark the new statement with
        """

        if labels is None:
            self.labels = []
        else:
            self.labels = list(labels)

    def __str__(self):
        return "".join(lab + ":\n" for lab in self.labels)


class Instruction(Statement):
    """A parsed assembly instruction."""

    class ImmediateConstant:
        """
        An immediate constant.

        This class represents some sort of constant used as an immediate value by an instruction.
        Such constant can be a literal value or a symbolic one.
        Immediate formats can differ in size, so a size must be specified at creation time for faithful representation
        and correct manipulation of the binary value.

        :var symbol: the symbolic identifier of the constant, if any
        :var value: the binary representation of the value, if assigned
        :var int_val: the integer representation of the value, if assigned
        :var size: the size in bits of the containing immediate field
        """

        _symbol: Optional[str]
        _value: Optional[BitVector]
        _size: int

        def __init__(self, size, symbol: str = None, value: int = None):
            """
            Instantiate an immediate constant of the specified size and value, identified by a symbol.

            :param size: the size in bits of the constant
            :param symbol: the symbol identifying the constant, if any
            :param value: the integer value of the constant, if any
            :raise ValueError: when both symbol and value are left unspecified
            """

            if symbol is None and value is None:
                raise ValueError("Constant must be symbolic or have a value")

            self._size = size
            self._symbol = symbol

            if value is not None:

                # Prepare the mask for cutting the supplied value's bit representation to the specified size
                mask = 0
                for f in range(0, size):
                    mask += 2 ** f

                value = value & mask
                self._value = BitVector(intVal=value, size=size)

                # Sizes must be coherent
                assert self._size == len(self._value)
            else:
                self._value = None

        @property
        def symbol(self) -> str:
            return self._symbol

        @property
        def value(self) -> BitVector:
            return self._value.deep_copy()

        @property
        def int_val(self) -> int:
            # Return the constant's integer representation, preserving its sign through an overly complicated procedure
            return -((~self._value).int_val() + 1) if self._value[0] == 1 else self._value.int_val()

        @property
        def size(self):
            return self._size

        def __repr__(self):
            return "Instruction.ImmediateConstant(size=" + repr(self._size) + ", symbol=" + repr(self._symbol) + \
                   ", value=" + repr(None if self._value is None else self.int_val) + ")"

        def __str__(self):
            return str(self.int_val) if self._symbol is None else self.symbol

    opcode: str
    family: str
    r1: Optional[Register]
    r2: Optional[Register]
    r3: Optional[Register]
    immediate: Optional[ImmediateConstant]

    def __init__(self, opcode: str, family: str, labels: Sequence[str] = None, r1: Union[str, Register] = None,
                 r2: Union[str, Register] = None, r3: Union[str, Register] = None,
                 immediate: Union[str, int, ImmediateConstant] = None):
        """
        Instantiates a new instruction statement.

        :param opcode: the opcode of the new instruction
        :param family: the instruction's format
        :param labels: an optional list of labels to mark the instruction with
        :param r1: the first register parameter, if any
        :param r2: the second register parameter, if any
        :param r3: the third register parameter, if any
        :param immediate: the immediate constant passed to the function, if any
        """

        # Clean register arguments from the 'unused' keyword and raise an exception if a 'reg_err' is found
        if r1 == "reg_err" or r2 == "reg_err" or r3 == "reg_err":
            raise ValueError("Received the output of a failed parsing pass")

        r1 = r1 if r1 != "unused" else None
        r2 = r2 if r2 != "unused" else None
        r3 = r3 if r3 != "unused" else None

        super().__init__(labels)
        self.opcode = opcode
        self.family = family
        self.r1 = Register[r1.upper()] if type(r1) is str else r1
        self.r2 = Register[r2.upper()] if type(r2) is str else r2
        self.r3 = Register[r3.upper()] if type(r3) is str else r3

        if family in imm_sizes:
            if isinstance(immediate, int):
                # Constant as literal value
                self.immediate = Instruction.ImmediateConstant(value=immediate,
                                                               size=imm_sizes[family])
            elif isinstance(immediate, str):
                # Constant as symbolic value
                self.immediate = Instruction.ImmediateConstant(symbol=immediate,
                                                               size=imm_sizes[family])
            else:
                # Maybe an ImmediateConstant itself
                self.immediate = immediate
        else:
            self.immediate = None

    def __repr__(self):
        return "Instruction(" + repr(self.opcode) + ", " + repr(self.family) + ", " + repr(self.labels) + ", " + \
               repr(self.r1) + ", " + repr(self.r2) + ", " + repr(self.r3) + ", " + repr(self.immediate) + ")"

    def __str__(self):
        return super().__str__() + familystr[self.family](self)


class Directive(Statement):
    """A parsed assembler directive."""

    name: str
    args: Sequence[str]

    def __init__(self, name: str, labels: Optional[Sequence[str]] = None, args: Optional[Sequence[str]] = None):
        """
        Instantiates a new assembler directive statement.

        :param name: the directive's name
        :param labels: an optional list of labels to mark the directive with
        :param args: an optional sequence of arguments for the directive
        """

        super().__init__(labels)
        self.name = name

        if args is None:
            self.args = []
        else:
            self.args = list(args)

    def __repr__(self):
        return "Directive(" + repr(self.name) + ", " + repr(self.labels) + ", " + repr(self.args) + ")"

    def __str__(self):
        # TODO investigate correctness of this string representation
        return super().__str__() + "\t" + str(self.name) + "\t" + ", ".join(self.args) + "\n"


class ASMLine(NamedTuple):
    """An assembler source line."""

    number: int
    statement: Statement


def to_line_iterator(statement_iterator: Iterator[Statement], starting_line: int = 0) -> Iterator[ASMLine]:
    """
    Wrap an iterator over statements to make it an iterator over assembly lines.

    For every statement returned by the wrapped iterator, an ASMLine object is made out of it, incrementing the line
    number starting from the provided one, or 0 by default.

    :param statement_iterator: the iterator to be wrapped
    :param starting_line: the line number from which line numbering will start
    :return: an iterator over ASM lines
    """

    current_line = starting_line
    for statement in statement_iterator:
        yield ASMLine(current_line, statement)
        current_line += 1


# Mapping contributed by Alessandro Nazzari (https://github.com/zoythum)

# This is a classification of all the possible opcodes.
# Each opcode is paired with a tuple (<int>, <boolean>) where the int value represents the number of registers used
# by that specific opcode, the boolean value instead tells if we are dealing with a write function (True)
# or a read only one (False)
opcodes: Mapping[str, Tuple[int, bool]] = {
    'lui': (1, True), 'auipc': (1, True), 'jal': (1, True), 'jalr': (2, True), 'lb': (2, True), 'lh': (2, True),
    'lw': (2, True), 'lbu': (2, True), 'lhu': (2, True), 'addi': (2, True), 'slti': (2, True),
    'sltiu': (2, True), 'xori': (2, True), 'ori': (2, True), 'andi': (2, True), 'slli': (2, True),
    'srli': (2, True), 'srai': (2, True), 'lwu': (2, True), 'ld': (2, True), 'addiw': (2, True),
    'slliw': (2, True), 'srliw': (2, True), 'sext.w': (2, True), 'mv': (2, True), 'sraiw': (2, True), 'lr.w': (2, True),
    'lr.d': (2, True), 'add': (3, True), 'sub': (3, True), 'sll': (3, True), 'slt': (3, True),
    'sltu': (3, True), 'xor': (3, True), 'srl': (3, True), 'sra': (3, True), 'or': (3, True), 'and': (3, True),
    'addw': (3, True), 'subw': (3, True), 'sllw': (3, True), 'srlw': (3, True), 'sraw': (3, True), 'mul': (3, True),
    'mulh': (3, True), 'mulhsu': (3, True), "mulhu": (3, True), 'div': (3, True), 'divu': (3, True), 'rem': (3, True),
    'remu': (3, True), 'mulw': (3, True), 'divw': (3, True), 'divuw': (3, True), 'remw': (3, True),
    'remuw': (3, True), 'sc.w': (3, True), 'amoswap.w': (3, True), 'amoadd.w': (3, True),
    'amoxor.w': (3, True), 'amoor.w': (3, True), 'amoand.w': (3, True), 'amomin.w': (3, True), 'amomax.w': (3, True),
    'amominu.w': (3, True), 'amomaxu.w': (3, True), 'sc.d': (3, True), 'amoswap.d': (3, True), 'amoadd.d': (3, True),
    'amoxor.d': (3, True), 'amoor.d': (3, True), 'amoand.d': (3, True), 'amomin.d': (3, True),
    'amomax.d': (3, True), 'amominu.d': (3, True), 'amomaxu.d': (3, True), 'jr': (1, False), 'j': (0, False),
    'beq': (2, False), 'bne': (2, False), 'blt': (2, False), 'bge': (2, False), 'ble': (2, False), 'bltu': (2, False),
    'bgeu': (2, False), 'sb': (2, False), 'sh': (2, False), 'sw': (2, False), 'sd': (2, False), 'li': (1, True),
    'beqz': (1, False), 'bnez': (1, False), 'blez': (1, False),
    'bgez': (1, False), 'bgtu': (2, False), 'bleu': (2, False), 'nop': (0, False), 'call': (0, False)
}

# Mapping contributed by Mattia Iamundo (https://github.com/MattiaIamundo)

# This is a mapping that, for each instruction, associate the relative family name
opcd_family: Mapping[str, str] = {
    'add': 'r', 'addw': 'r', 'and': 'r', 'or': 'r', 'sext.w': 'sext', 'sll': 'r', 'sllw': 'r', 'sub': 'r', 'subw': 'r',
    'xor': 'r', 'xori': 'i', 'jr': 'jr', 'j': 'j', 'beqz': 'bz', 'bnez': 'bz', 'nop': 'nop', 'blez': 'bz', 'beq': 'b',
    'bge': 'b', 'bgeu': 'b', 'blt': 'b', 'ble': 'b', 'bltu': 'b', 'bne': 'b', 'bgt': 'b', 'bgez': 'bz', 'bltz': 'bz',
    'bleu': 'b', 'addi': 'i', 'addiw': 'i', 'andi': 'i', 'auipc': 'u', 'jal': 'j', 'jalr': 'jr', 'ori': 'i',
    'slli': 'i', 'slliw': 'i', 'slt': 'r', 'slti': 'i', 'sltiu': 'i', 'sltu': 'r', 'sra': 'r', 'sraw': 'r', 'srai': 'i',
    'sraiw': 'i', 'srl': 'r', 'srlw': 'r', 'srli': 'i', 'srliw': 'i', 'mul': 'r', 'mulh': 'r', 'mulhsu': 'r',
    'mulhu': 'r', 'div': 'r', 'divu': 'r', 'rem': 'r', 'remu': 'r', 'mulw': 'r', 'divw': 'r', 'divuw': 'r', 'remw': 'r',
    'remuw': 'r', 'lr.w': 'al', 'lb': 'i', 'lbu': 's', 'lh': 's', 'lui': 'u', 'lw': 's', 'sb': 's', 'sh': 's',
    'sw': 's', 'call': 'j', 'sd': 's', 'mv': '_2arg', 'ld': 's', 'li': 'li', 'bgtu': 'b', 'lwu': 's', 'lhu': 's',
    'not': '_2arg', 'negw': '_2arg', 'sc.w': 'as', 'amoswap.w': 'as', 'amoadd.w': 'as', 'amoxor.w': 'as',
    'amoor.w': 'as', 'amoand.w': 'as', 'amomin.w': 'as', 'amomax.w': 'as', 'amominu.w': 'as', 'amomaxu.w': 'as',
    'lr.d': 'al', 'sc.d': 'as', 'amoswap.d': 'as', 'amoadd.d': 'as', 'amoxor.d': 'as', 'amoand.d': 'as',
    'amomin.d': 'as', 'amomax.d': 'as', 'amominu.d': 'as', 'amomaxu.d': 'as', 'bgtz': 'bz', 'snez': 'snez'
}
