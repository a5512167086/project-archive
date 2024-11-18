CREATE OR REPLACE FUNCTION fs_check_bitwise(_bit_value BIGINT, _bit_position SMALLINT)
    RETURNS BOOLEAN
    AS $$
DECLARE
    compare_value BIGINT :=(2 ^ _bit_position);
    output BOOLEAN := FALSE;
BEGIN
    IF (_bit_value & compare_value) = compare_value THEN
        output := TRUE;
    ELSE
        output := FALSE;
    END IF;
    RETURN output;
END;
$$
LANGUAGE plpgsql;

