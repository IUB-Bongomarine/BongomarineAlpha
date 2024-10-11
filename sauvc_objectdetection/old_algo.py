def find_rectangle_right(img, frame, h):
    original = frame.copy()

    contours, _hierarchy = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    #print("number of countours: %d" % len(contours))

    rectangle_list = []

    for cnt in contours:
        rectangle_list += [Rectangle(cnt)]

    # Sorting by their area.
    rectangle_list.sort(key=lambda x : x.area, reverse = True)      

    # Validation check : Not enough rectangle
    if len(rectangle_list) < 2:
        gate_info = (most_possible_gate[0].left_top_pt, most_possible_gate[1].right_bottom_pt, gate_area, gate_mid_pt)
        return None

    # Only consider the largest 4 rectangles
    possible_gate = []
    if len(rectangle_list) >= 4:
        for i in range(4):      
            if rectangle_list[i].slope == -1 or rectangle_list[i].slope > 11:               #tan(85) = 11  
                possible_gate += [rectangle_list[i]]
    else:
        possible_gate = rectangle_list

    # Validation check : Not enough rectangle
    if len(possible_gate) < 2:  
        return None

    # The lower/larger, the foremost (the possibility that it is underwater is higher)
    possible_gate.sort(key=lambda x : x.left_top_pt[1], reverse=True)       
    #print("number of possible recantagle for gate: ", len(possible_gate))

    # Validation check : Prevent that one rectangle is on the top (shadow) and one rectangle is  underwater
    if abs(possible_gate[0].left_top_pt[1] - possible_gate[1].left_top_pt[1]) > 150 :
        return None

    # Only consider the lowest two.
    most_possible_gate = []
    for i in range(2):
        most_possible_gate += [possible_gate[i]]

    # Sorting them accoring to x coordinate
    most_possible_gate.sort(key=lambda x : x.left_top_pt[0]) 
    
    # Validation check : whether the gate area is too small
    length = (most_possible_gate[1].right_bottom_pt[0] - most_possible_gate[0].left_top_pt[0]) #x
    width = (most_possible_gate[1].right_bottom_pt[1] - most_possible_gate[0].left_top_pt[1]) #y
    gate_area = length * width 
    if gate_area <= 10000:
        return None

    gate_mid_pt = (most_possible_gate[0].left_top_pt[0] + int(length / 2), most_possible_gate[0].left_top_pt[1] + int(width / 2))
    
    gate_info = (most_possible_gate[0].left_top_pt, most_possible_gate[1].right_bottom_pt, gate_area, gate_mid_pt)
    print("gate_info:", gate_info)

    # Drawing the rectangles
    for  rectangle in most_possible_gate:
        original = rectangle.drawing(original)  
    cv2.imshow('left_rectangle',original)
    cv2.waitKey(0)

    return gate_info