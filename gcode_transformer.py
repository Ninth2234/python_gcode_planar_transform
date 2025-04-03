from gcodeparser import GcodeParser,Commands
import numpy as np




def get_total_lines(parser:GcodeParser):
    return len(parser.lines)

def query_comment_marker(parser:GcodeParser,marker:str)->int:
    for i in range(len(parser.lines)):
        if parser.lines[i].comment == marker:
            return i

def transform_gcode(parser:GcodeParser, transform_matrix: np.ndarray, start_idx=None, stop_idx=None)->GcodeParser:
    output = GcodeParser(parser.gcode,True)
    x_cur,y_cur,z_cur = [None,None,None]
    for i in range(len(parser.lines)):
        line = parser.lines[i]

        if line.type != Commands.MOVE:
            continue

        x_cur = line.params.get('X', x_cur)
        y_cur = line.params.get('Y', y_cur)
        z_cur = line.params.get('Z', z_cur)

        x_tf,y_tf,z_tf = [x_cur,y_cur,z_cur]

        if i < start_idx or i>stop_idx:
            continue

        if any(axis in line.params for axis in ('X','Y','Z')):
            cur_pt = np.array([x_cur, y_cur, 1])
            tf_pt = np.matmul(transform_matrix,cur_pt)
            x_tf = tf_pt[0]/tf_pt[2]
            y_tf = tf_pt[1]/tf_pt[2]
        
            output.lines[i].params.update({'X':x_tf,'Y':y_tf})
        
    return output

def create_transform_matrix(theta_deg, x, y):
    cos_t = np.cos(np.radians(theta_deg))
    sin_t = np.sin(np.radians(theta_deg))
    
    transform_matrix = np.array([
        [cos_t, -sin_t, x],
        [sin_t, cos_t, y],
        [0, 0, 1]
    ])
    
    return transform_matrix


if __name__ == "__main__":

    START_MARKER = "START_TRANSFORM"
    STOP_MARKER = "STOP_TRANSFORM"

    # Read the input G-code file
    input_file = 'S2A_Print_test_with_casting v1_base_21min.gcode'
    output_file = f'Transformed_{input_file}'

    X_SHIFT = 50
    Y_SHIFT = 50
    THETA_SHIFT = 45

    with open(input_file, 'r') as f:
        gcode = f.read()

    # Parse the G-code
    parser = GcodeParser(gcode,True)

    total_lines = get_total_lines(parser)
    start_idx = query_comment_marker(parser,START_MARKER)
    stop_idx = query_comment_marker(parser,STOP_MARKER)

    if start_idx is None:
        raise ValueError(f"Start marker not found in the G-code ({START_MARKER}).")
    if stop_idx is None:
        raise ValueError(f"Stop marker not found in the G-code ({STOP_MARKER}).")

    tf_parser = transform_gcode(parser,create_transform_matrix(THETA_SHIFT,X_SHIFT,Y_SHIFT),start_idx,stop_idx)

    tf_parser.lines[start_idx].comment = f'{START_MARKER} SHIFT X:{X_SHIFT}, Y:{Y_SHIFT}, theta:{THETA_SHIFT}'
    tf_parser.lines[stop_idx].comment = f'{STOP_MARKER} SHIFT X:{X_SHIFT}, Y:{Y_SHIFT}, theta:{THETA_SHIFT}'


    with open(output_file, 'w') as f:
        for line in tf_parser.lines:
            f.write(str(line.gcode_str) + '\n')  # Convert each line to string and write
    print()
    print("_"*40)
    print(f"Reading: {input_file}")
    print(f"Transform to X:{X_SHIFT}, Y:{Y_SHIFT}, THETA:{THETA_SHIFT}")
    print(create_transform_matrix(THETA_SHIFT,X_SHIFT,Y_SHIFT))
    print("_"*40)
    print(f"Transformed G-code written to {output_file}")

