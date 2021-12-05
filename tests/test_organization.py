from rename_file import RenameFile


def check_for_file(filename, foldername, RF, checking):
    val = RF.find_file(filename, foldername)
    print(val)
    assert val == checking

from datetime import datetime
if __name__ == '__main__':
    rf = RenameFile()
    final_path = "/Users/raveena/Desktop/testing_org/Fall 2021 CS 30700-LE1 LEC/LEC-03.pdf"
    check_for_file("LEC-03.pdf", "/Users/raveena/Desktop/testing_org", rf, final_path)

    final_path = "/Users/raveena/Desktop/testing_org/Fall 2021 CS 30700-LE1 LEC/LEC-06.pdf"
    check_for_file("LEC-06.pdf", "/Users/raveena/Desktop/testing_org", rf, final_path)

    final_path = "/Users/raveena/Desktop/testing_org/Fall 2021 CS 30700-LE1 LEC/LEC-04.pdf"
    check_for_file("LEC-04.pdf", "/Users/raveena/Desktop/testing_org", rf, final_path)

    final_path = "/Users/raveena/Desktop/testing_org/Fall 2021 CS 30700-LE1 LEC/LEC-05.pdf"
    check_for_file("LEC-05.pdf", "/Users/raveena/Desktop/testing_org", rf, final_path)

    final_path = "/Users/raveena/Desktop/testing_org/Fall 2021 CS 30700-LE1 LEC/LEC-07.pdf"
    check_for_file("LEC-07.pdf", "/Users/raveena/Desktop/testing_org", rf, final_path)

    final_path = "/Users/raveena/Desktop/testing_org/Fall 2021 CS 30700-LE1 LEC/fall17_sprintplanning_elementrium.pdf"
    check_for_file("fall17_sprintplanning_elementrium.pdf", "/Users/raveena/Desktop/testing_org", rf, final_path)

    print("Everything passed")
