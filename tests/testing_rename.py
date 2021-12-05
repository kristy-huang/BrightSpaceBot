from rename_file import RenameFile


def valid_file_name(newFileName, oldFileName, RF):
    split = oldFileName.rsplit('/', 1)  # splits from last slash from the back
    extension = oldFileName.rsplit(".", 1)[1]  # get the file extension
    status, rename = RF.contains_extension(newFileName, extension)
    if not status:
        # the requested path was not valid
        return False
    else:
        return True


if __name__ == '__main__':
    rf = RenameFile()
    assert valid_file_name("testing.pdf", "texting.txt", rf) == False

    assert valid_file_name("testing.pdf", "texting.pdf", rf) == True

    assert valid_file_name("testing", "texting.txt", rf) == True

    assert valid_file_name("testing.roro", "texting.txt", rf) == False

    assert valid_file_name("testing.....", "texting.txt", rf) == False

    assert valid_file_name("testing.pdf.pdf.pdf", "texting.txt", rf) == False

    assert valid_file_name("testing.txt", "texting.txt", rf) == True

    # MAKE SURE TO RESET WHEN TESTING
    assert rf.rename_file_local("/Users/raveena/Desktop/rename_test/307/HW4.txt", "homework4") == True
    assert rf.rename_file_local("/Users/raveena/Desktop/rename_test/307/homework4.txt", "homework4.pdf") == False
    assert rf.rename_file_local("/Users/raveena/Desktop/rename_test/307/homework4.txt", "HW4") == True

    print("Everything passed")
