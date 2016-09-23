import bslint.error_messages_builder.error_message_handler as err
import re
from bslint import constants as const
import bslint.utilities.commands as commands


class MatchHandler:
    def __init__(self, characters):
        self._is_empty_line = True
        self._line_not_to_style_check = -1
        self.line_number = 1
        self.characters = characters
        self._consecutive_empty_lines = 0
        self._indentation_level = 0
        self.line_length = 0
        self.current_char_index = 0
        self._current_indentation_level = 0
        self._skip_styling_on_file = False
        self._match = None
        self._token_type = None
        self.warnings = []

    def _get_last_line(self):
        last_line = re.findall("(?:(?<=^)|(?<=\n))(.*)", self.characters[:self.current_char_index - 1], re.MULTILINE)
        return last_line[-1]

    def match_handler(self, regex_match):
        self._match = regex_match["match"]
        self._token_type = regex_match["token_type"]

        if regex_match["indentation_level"] != const.NO_INDENTATION:
            self._indentation_level = regex_match["indentation_level"]

        self._apply_styling()
        token_tuple = None
        if self._token_type == const.NEW_LINE:
            self.line_number += 1
        elif self._token_type == const.BSLINT_COMMAND:
            self._apply_bslint_command()
        elif self._token_type != const.COMMENT:
            token_tuple = self._build_token()
        return token_tuple

    def _apply_bslint_command(self):
        command_type = self._match.group('command')
        if command_type == "skip_line":
            self._line_not_to_style_check = commands.check_skip_line(self.line_number)
        elif command_type == "skip_file":
            self._skip_styling_on_file = commands.check_skip_file()

    def _apply_styling(self):
        if self.style_checking_is_active():
            if self._token_type is const.NEW_LINE:
                self.apply_new_line_styling()
            else:
                self._apply_common_styling()

    def style_checking_is_active(self):
        return self.line_number != self._line_not_to_style_check and not self._skip_styling_on_file

    def check_trace_free(self):
        is_trace_free = commands.check_trace_free()
        self._warning_filter(is_trace_free)

    def _apply_common_styling(self):
        self._is_empty_line = False
        if self._token_type == const.COMMENT:
            self._check_comment_styling()
        elif self._token_type == const.OPERATOR:
            self._check_operator_spacing()
        elif self._token_type == const.ID:
            self._check_spelling()
        elif self._token_type == const.PRINT_KEYWORD:
            self.check_trace_free()

    def _check_spelling(self):
        is_spelt_correctly = commands.check_spelling(self._match.group(), self._token_type)
        self._warning_filter(is_spelt_correctly)

    def _check_operator_spacing(self):
        correct_spacing = commands.check_spaces_around_operators(self.characters, self.current_char_index)
        self._warning_filter(correct_spacing)

    def _check_comment_styling(self):
        is_correct_comment = commands.check_comment(self._match.group())
        self._warning_filter(is_correct_comment)
        self._check_spelling()

    def apply_new_line_styling(self):
        self._count_consecutive_new_lines()
        is_correct_line_length = commands.check_max_line_length(self.line_length)
        self._warning_filter(is_correct_line_length)

        is_consecutive_empty_lines = commands.check_consecutive_empty_lines(self._consecutive_empty_lines)
        self._warning_filter(is_consecutive_empty_lines)

        last_read_line = self._get_last_line()
        self._apply_indentation_styling(last_read_line)
        is_correct_method_declaration_spacing = commands.check_method_declaration_spacing(last_read_line)
        self._warning_filter(is_correct_method_declaration_spacing)
        self.line_length = 0

    def _apply_indentation_styling(self, last_read_line):
        is_correct_indentation = commands.check_indentation(self._current_indentation_level, last_read_line,
                                                            self._indentation_level)
        if is_correct_indentation:
            self._warning_filter(is_correct_indentation[0])
            self._current_indentation_level = is_correct_indentation[1]
            self._indentation_level = 0

    def _count_consecutive_new_lines(self):
        if self._is_empty_line is True:
            self._consecutive_empty_lines += 1
        else:
            self._is_empty_line = True
            self._consecutive_empty_lines = 0

    def _build_token(self):
        if self._token_type == const.STRING:
            tuple_token = self._build_string_tuple()
        elif self._token_type == const.ID:
            tuple_token = self._build_id_tuple()
        else:
            tuple_token = (self._match.group(), self._token_type)
        return tuple_token + (self.line_number,)

    def _build_string_tuple(self):
        group = self._match.group()
        return group[1:-1], self._token_type

    def _build_id_tuple(self):
        group = self._match.group('value')
        tuple_token = (group, self._token_type)
        if self._match.group('type') is not '':
            tuple_token = (group, self._token_type, self._match.group('type'))
        return tuple_token

    def _warning_filter(self, result):
        if result is not None:
            result["error_params"].append(str(self.line_number))
            warning = err.get_message(result["error_key"], result["error_params"])
            self.warnings += [warning]