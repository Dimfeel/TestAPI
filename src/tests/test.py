import json

def test():
    with open("data.json") as file:
        a = json.load(file)
    print(a)
    
if __name__ == "__main__":
    test()