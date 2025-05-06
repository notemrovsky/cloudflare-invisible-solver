import json


def encode(input_data, encoding_key_string):
    if input_data is None:
        return ""

    if isinstance(input_data, (dict, list, tuple)):
        input_data_str = json.dumps(input_data, separators=(",", ":"))
    else:
        input_data_str = str(input_data)

    return _lzw_encode_to_key_chars(
        input_data_str, 6, lambda code: encoding_key_string[code]
    )


def _lzw_encode_to_key_chars(
    input_string, output_char_bit_size, get_char_from_code_func
):
    dictionary = {}
    single_char_map = {}

    current_sequence_buffer = ""
    codes_until_bit_len_increase = 2
    next_available_code = 3
    current_code_bit_length = 2

    output_char_list = []
    bit_accumulator = 0
    bits_in_accumulator = 0

    def write_code_bits(value, num_bits):
        nonlocal bit_accumulator, bits_in_accumulator
        for _ in range(num_bits):
            bit = value & 1
            bit_accumulator = (bit_accumulator << 1) | bit
            bits_in_accumulator += 1
            if bits_in_accumulator == output_char_bit_size:
                output_char_list.append(get_char_from_code_func(bit_accumulator))
                bit_accumulator = 0
                bits_in_accumulator = 0
            value >>= 1

    for char_in_input in input_string:
        if char_in_input not in dictionary:
            dictionary[char_in_input] = next_available_code
            next_available_code += 1
            single_char_map[char_in_input] = True

        extended_sequence = current_sequence_buffer + char_in_input

        if extended_sequence in dictionary:
            current_sequence_buffer = extended_sequence
        else:
            if current_sequence_buffer in single_char_map:
                char_ord_value = ord(current_sequence_buffer[0])
                if char_ord_value < 256:
                    write_code_bits(0, current_code_bit_length)
                    write_code_bits(char_ord_value, 8)
                else:
                    write_code_bits(1, current_code_bit_length)
                    write_code_bits(char_ord_value, 16)

                codes_until_bit_len_increase -= 1
                if codes_until_bit_len_increase == 0:
                    codes_until_bit_len_increase = 2**current_code_bit_length
                    current_code_bit_length += 1

                if current_sequence_buffer in single_char_map:
                    del single_char_map[current_sequence_buffer]
            else:
                write_code_bits(
                    dictionary[current_sequence_buffer], current_code_bit_length
                )

            codes_until_bit_len_increase -= 1
            if codes_until_bit_len_increase == 0:
                codes_until_bit_len_increase = 2**current_code_bit_length
                current_code_bit_length += 1

            dictionary[extended_sequence] = next_available_code
            next_available_code += 1
            current_sequence_buffer = char_in_input

    if current_sequence_buffer != "":
        if current_sequence_buffer in single_char_map:
            char_ord_value = ord(current_sequence_buffer[0])
            if char_ord_value < 256:
                write_code_bits(0, current_code_bit_length)
                write_code_bits(char_ord_value, 8)
            else:
                write_code_bits(1, current_code_bit_length)
                write_code_bits(char_ord_value, 16)

            codes_until_bit_len_increase -= 1
            if codes_until_bit_len_increase == 0:
                codes_until_bit_len_increase = 2**current_code_bit_length
                current_code_bit_length += 1

            if current_sequence_buffer in single_char_map:
                del single_char_map[current_sequence_buffer]
        else:
            write_code_bits(
                dictionary[current_sequence_buffer], current_code_bit_length
            )
            codes_until_bit_len_increase -= 1
            if codes_until_bit_len_increase == 0:
                current_code_bit_length += 1

    write_code_bits(2, current_code_bit_length)
    bit_accumulator <<= output_char_bit_size - bits_in_accumulator
    output_char_list.append(get_char_from_code_func(bit_accumulator))

    return "".join(output_char_list)
