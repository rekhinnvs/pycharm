''' Script to fill the sdcard memory to 95%'''
import subprocess

actual_size = used_size = percentage_filled = ''
value_95 = 0
sd_card_name = '/sdcard'

def get_size():
    cmd_adb_shell_df = 'adb shell df | grep storage'
    child = subprocess.Popen(cmd_adb_shell_df, shell=True, stdout=subprocess.PIPE)
    temp = child.communicate()[0]
    output = temp.split()
    global sd_card_name, percentage_filled
    #percentage_filled = output[]
    #sd_card_name = output[-1]


def fill_data():
    global sd_card_name, percentage_filled
    count = 0
    while percentage_filled != '95%':
        cmd_fill = 'adb shell dd if=/dev/zero of=' + sd_card_name + '/file' + str(count) + '.txt count=1024 bs=1024'
        child = subprocess.Popen(cmd_fill, shell=True, stdout=subprocess.PIPE)
        child.communicate()[0]
        print 'filling ' + percentage_filled
        get_size()
        count += 1
    print "filled 95% of data, exiting..."
    quit()


get_size()
fill_data()