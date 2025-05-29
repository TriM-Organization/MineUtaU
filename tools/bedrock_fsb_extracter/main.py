
# 可以在
# https://github.com/Mojang/bedrock-samples/tree/main/resource_pack/sounds
# 找到基岩版原版音效文件
# 
# 这里有音效定义的 json
# https://github.com/Mojang/bedrock-samples/raw/refs/heads/main/resource_pack/sounds/sound_definitions.json
# 

# 在维基
# https://zh.minecraft.wiki/w/%E5%9F%BA%E5%B2%A9%E7%89%88%E5%A3%B0%E9%9F%B3%E4%BA%8B%E4%BB%B6
# 查阅相关内容之定义

for sound in open("sound_definitions.json"):
    print(sound)


