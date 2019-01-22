from sys import argv
import importlib

if __name__ == "__main__":
    if len(argv) > 1:
        demo_name = "demos." + argv[1]
        print(demo_name)

        importlib.import_module(demo_name).main()

    else:
        print("please supply the name of demo module")
