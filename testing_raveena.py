from bs_api import BSAPI
from bs_utilities import BSUtilities


def test_path_is_valid(bs_utils, path, drive):
    ret_val = bs_utils.validate_path_drive(path, drive)
    return ret_val


if __name__ == "__main__":
    bs_utils = BSUtilities()
    drive = bs_utils.init_google_auths()

    assert test_path_is_valid(bs_utils, "/Users/raveena/Desktop/testing", drive) == True
    assert test_path_is_valid(bs_utils, "/Some/Rando/Directory", drive) == False
    assert test_path_is_valid(bs_utils, "test", drive) == True
    assert test_path_is_valid(bs_utils, "google docs", drive) == False

    print("Everything passed")