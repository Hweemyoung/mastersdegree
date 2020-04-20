import json

if __name__ == '__main__':
    with open('channel_ids_AI.txt') as f:
      channel_list = json.load(f)
    print(channel_list[0].values())
    for chan_id in channel_list[0].values():
        print(chan_id)