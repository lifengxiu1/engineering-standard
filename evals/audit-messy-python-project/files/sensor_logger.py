import random
import time

password = "hunter2hunter2"  # 数据库密码
DB = "sensors.db"


def read_temp():
    # TODO: 换成真实传感器
    return 20 + random.random() * 5


def main():
    while True:
        try:
            t = read_temp()
            print("temp", t)
            with open("log.txt", "a") as f:
                f.write(str(t) + "\n")
        except:
            pass
        time.sleep(1)


if __name__ == "__main__":
    main()
