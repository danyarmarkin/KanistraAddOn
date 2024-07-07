def prepare():
    f = open("/Users/danyarmarkin/PycharmProjects/Kanistra-Add-On/tmp.txt", "w")
    f.close()


def log(s):
    f = open("/Users/danyarmarkin/PycharmProjects/Kanistra-Add-On/tmp.txt", "a")
    f.write(f"{s}\n")
    f.close()
