import subprocess

actual_size = used_size = percentage_filled = ''
value_95 = 0
sd_card_name = ''


def get_size():
    cmd_adb_shell_df = 'adb shell df | grep storage'
    child = subprocess.Popen(cmd_adb_shell_df, shell=True, stdout=subprocess.PIPE)
    temp = child.communicate()[0]
    output = temp.split()
    global sd_card_name
    if len(output) < 7:
        print "Looks like there is no SD card inserted!. How about inserting one?"
        quit()
    else:
        # actual_size = output[7]
        # used_size = output[8]
        # percentage_filled = output[10]
        # value_95 = int((int(actual_size) * .95)/1024)
        sd_card_name = output[-1]
        ##print actual_size, used_size, percentage_filled
        # print value_95
        print "getsize_sdcard_value", sd_card_name
        # return used_size,value_95,percentage_filled


def fill_data():
    global sd_card_name
    count = 0
    while percentage_filled != '95%':
        print percentage_filled

        print "sdcard name", sd_card_name
        cmd_fill = 'adb shell dd if=/dev/zero of=' + sd_card_name + '/file' + str(count) + '.txt count=1024 bs=1024'
        print cmd_fill
        child = subprocess.Popen(cmd_fill, shell=True, stdout=subprocess.PIPE)
        child.communicate()[0]
        print 'filling' + percentage_filled
        get_size()
        count += 1
    print "filled 95% of data, exiting..."
    quit()


get_size()
fill_data()