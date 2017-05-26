#!/usr/bin/python
import sys
import commands
import time
import inspect
import thread
import os
import StringIO
import subprocess
import util
import preference
import logger
# import db
import reporter
import configurator
import testexecutor
import common
import exceptions
import string
import re

# import chromdriver

INTERVAL_TIME = 10
PHONE_INTERVAL_TIME = 30

g_Current_testClass = ''
g_Current_testMethod = ''
g_Current_testPackage = ''
g_Current_testRunner = ''
g_jarName = ''
g_cmd_prepared = ''
g_collect_bugreport = ''
PROJECT_NAME = 'com.example.android.testing.uiautomator.BasicS'
UIAUTOMATOR_EXTRA_COMMAND = ' com.example.android.testing.uiautomator.BasicSample.test/android.support.test.runner.AndroidJUnitRunner'
LOOP_COUNTER_STRING = 'numOfLoops'
ADBCMD_1_EXTRA = 'adb -s %s shell am instrument -e class %s -w %s'
ADBCMD_UIAUTOMATOR_NO_LOOP = 'adb -s %s shell uiautomator runtest %s -c %s'
ADBCMD_2_EXTRAS = 'adb -s %s shell am instrument -e class %s -e ' + LOOP_COUNTER_STRING + ' xxx' + ' -w %s'
ADBCMD_UIAUTOMATOR = 'adb -s %s shell am instrument -w -r -e numOfLoops xxx -e debug false -e %s' + UIAUTOMATOR_EXTRA_COMMAND
ADBCMD_UIAUTOMATOR_YOUTUBE = 'adb -s %s shell uiautomator runtest %s -c %s -e ' + LOOP_COUNTER_STRING + ' xxx' + ' -e duration %s'
ADBCMD_UIAUTOMATOR_EXTRA = 'adb -s %s shell uiautomator runtest %s -c %s -e ' + LOOP_COUNTER_STRING + ' xxx' + ' -e extra_param %s'

REMARK_OK = ''
REMARK_FATAL = 'Aborted due to fatal error. '
REMARK_NON_FATAL = 'Some tests were NOT executed due to non fatal error. '
REMARK_NON_FATAL_ANR_OR_FC = 'Some tests were NOT executed due to ANR or FC in the process under test. '
REMARK_LESS_THAN_INTENDED = 'All intended tests were not run. '
REMARK_LOW_PASS_RATE = 'Pass rate is lower than expected. '
REMARK_DEVICE_RESET = 'Device has reset. Aborting... '
REMARK_DEVICE_DISCONNECTED_RETRY = 'ADB connection is lost and regained. Need to retry the remaining tests.'
REMARK_DEVICE_RETRY = 'Retrying the previous test...'
SUMMARY = 'Summary'
LOOP_SUMMARY = 'Loop Summary'


class StabilityCommandExecutionError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class StabilityDeviceTimeError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class StabilityDeviceRebootError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


g_loop_counter = 0
g_device_A_id = ''
g_device_B_id = ''
g_logger = None
g_db = None
g_reporter = None
g_mtbf_start_time = None

g_loop_intended_total = 0
g_loop_act_total = 0
g_loop_pass = 0
g_loop_fail = 0

g_testcase_intended_total = 0
g_testcase_act_total = 0
g_testcase_pass = 0
g_testcase_fail = 0
g_required_pass_rate = 95

g_device_start_time = 0
g_dummy_cmd = ''

g_device_id = ''
g_build_id = ''
g_product_name = ''
g_android_version = ''
g_uptime = ''
g_setupId = ''
g_collect_bugreport = ''

g_menu_nav_using_junit = configurator.IS_MENU_NAV_USING_JUNIT

g_to_be_retried = False
g_remaining_loop_count = 0
g_kill_processes = False
g_kill_All_Apps = False
g_Total_Pass = 0


def start(preference):
    global g_loop_counter, g_device_A_id, g_device_B_id, g_logger, g_reporter, g_mtbf_start_time
    global g_loop_intended_total, g_loop_act_total, g_loop_pass, g_loop_fail, g_kill_All_Apps
    global g_testcase_intended_total, g_testcase_act_total, g_testcase_pass, g_testcase_fail, g_required_pass_rate, g_device_start_time, g_kill_processes, g_db
    global g_tempCount, g_total_crashcount, g_loop_Crash, g_crash_text
    g_total_crashcount = 0
    g_crash_text = ''
    g_tempCount = 0
    g_loop_Crash = 0
    g_crash_text = ''

    bFlag = True
    g_loop_counter = 0
    g_device_A_id = ''
    g_device_B_id = ''
    excpVal = ''
    g_dummy_cmd = ''

    util.initOutput()  # Creates /Output dir
    util.setupLogging()

    g_kill_processes = configurator.KILL_PROCESSES_FLAG
    g_kill_All_Apps = configurator.KILL_ALL_APPS_FLAG

    g_device_A_id = configurator.PHONE_A_DEV_ID
    if 0 == util.checkDevice(g_device_A_id):
        util.pylogger.warn('@@@ FATAL ERROR-0 @@@ - Phone A not usable. Aborting...')
        return

    g_device_B_id = configurator.PHONE_B_DEV_ID
    if 0 == util.checkDevice(g_device_B_id):
        util.pylogger.warn('@@@ Phone B not usable. @@@')
        # return

    # Run the loops
    try:
        # g_db = db.Db()


        g_mtbf_start_time = getDeviceCurrentTime()
        if configurator.ENABLE_UPDATE_DASHBOARD:
            getDeviceDetails()
            setupRackInfoTable()
            setupSummaryTable()
        util.pylogger.warn(
            '===================================================================================================')
        util.pylogger.warn('========================================= Stability Script Version ' + str(
            configurator.Script_Version) + ' ============================')
        util.pylogger.warn(
            '===================================================================================================\n\n')

        util.pylogger.warn(
            '===================================================================================================')
        util.pylogger.warn(
            '========================================= START STABILITY =========================================')
        util.pylogger.warn(
            '===================================================================================================')
        g_device_start_time = util.getDeviceStartTime()
        util.pylogger.warn('Device Start Time - %s' % (str(g_device_start_time)))

        while bFlag:
            g_loop_counter = g_loop_counter + 1
            g_loop_intended_total = 0
            g_loop_act_total = 0
            g_loop_pass = 0
            g_loop_fail = 0
            g_loop_Crash = 0

            util.initLoopOutput(g_loop_counter)  # Creates /Output/Loop(x)
            g_logger = logger.Logger(g_loop_counter)  # Creates /Output/Loop(x)/Logs
            g_reporter = reporter.Reporter(g_loop_counter)  # Creates /Output/Loop(x)/Report and the report file

            start_time = getDeviceCurrentTime()
            util.pylogger.warn(
                '========================================= Loop - %d Start ==========================================' % (
                g_loop_counter))
            util.pylogger.warn('============================ Loop - %d Start time - %s ============================' % (
            g_loop_counter, str(start_time)))

            g_logger.collectMemInfo()
            g_logger.collectBatteryInfo()

            g_required_pass_rate = 95

            # 5.1.1 Telephony Stability Tests
            if preference.mIsAll or preference.mIsTelephony:
                g_testcase_intended_total = 0
                g_testcase_act_total = 0
                g_testcase_pass = 0
                g_testcase_fail = 0
                Telephony()

            # 5.1.2 Email Stability Tests
            if preference.mIsAll or preference.mIsEmail:
                g_testcase_intended_total = 0
                g_testcase_act_total = 0
                g_testcase_pass = 0
                g_testcase_fail = 0
                Email()

            # 5.1.3 Browser Stability Tests
            if preference.mIsAll or preference.mIsBrowser:
                g_testcase_intended_total = 0
                g_testcase_act_total = 0
                g_testcase_pass = 0
                g_testcase_fail = 0
                Browser()

            # 5.1.4 Store Front Stability Tests
            if preference.mIsAll or preference.mIsStoreFront:
                g_testcase_intended_total = 0
                g_testcase_act_total = 0
                g_testcase_pass = 0
                g_testcase_fail = 0
                StoreFront()

            # 5.1.5 PIM Stability Tests
            if preference.mIsAll or preference.mIsPIM:
                g_testcase_intended_total = 0
                g_testcase_act_total = 0
                g_testcase_pass = 0
                g_testcase_fail = 0
                g_required_pass_rate = 99
                PIM()
                g_required_pass_rate = 95

            # 5.1.6 Multi-Media Stability Tests
            if preference.mIsAll or preference.mIsMultimedia:
                g_testcase_intended_total = 0
                g_testcase_act_total = 0
                g_testcase_pass = 0
                g_testcase_fail = 0
                MultiMedia()

            # 5.1.7 Multi Tasking Stability Tests
            if preference.mIsAll or preference.mIsMultiTasking:
                g_testcase_intended_total = 0
                g_testcase_act_total = 0
                g_testcase_pass = 0
                g_testcase_fail = 0
                g_required_pass_rate = 99
                MultiTask()
                g_required_pass_rate = 95

            # 5.1.8 Menu Navigation
            if preference.mIsAll or preference.mIsMenuNav:
                g_testcase_intended_total = 0
                g_testcase_act_total = 0
                g_testcase_pass = 0
                g_testcase_fail = 0
                g_required_pass_rate = 99
                Menu_Nav()
                g_required_pass_rate = 95

            # 5.1.9 WiFi Stability Tests
            if preference.mIsAll or preference.mIsWiFi:
                g_testcase_intended_total = 0
                g_testcase_act_total = 0
                g_testcase_pass = 0
                g_testcase_fail = 0
                g_required_pass_rate = 99
                WiFi()
                g_required_pass_rate = 95

            # 5.1.12 Volte Stability Tests
            if preference.mIsAll or preference.mIsVoltecall:
                g_testcase_intended_total = 0
                g_testcase_act_total = 0
                g_testcase_pass = 0
                g_testcase_fail = 0
                g_required_pass_rate = 99
                VolteTelephony()
                g_required_pass_rate = 95

            # 5.1.14 Video Stability Tests
            if preference.mIsAll or preference.mIsVideocall:
                g_testcase_intended_total = 0
                g_testcase_act_total = 0
                g_testcase_pass = 0
                g_testcase_fail = 0
                g_required_pass_rate = 99
                VideoTelephony()
                g_required_pass_rate = 95

            # 5.1.14 Wi-fi calling Stability Tests
            if preference.mIsAll or preference.mIsWificall:
                g_testcase_intended_total = 0
                g_testcase_act_total = 0
                g_testcase_pass = 0
                g_testcase_fail = 0
                g_required_pass_rate = 99
                WifiCalling()
                g_required_pass_rate = 95

            end_time = getDeviceCurrentTime()
            remarks = REMARK_OK
            if g_loop_act_total != g_loop_intended_total:
                remarks = remarks + REMARK_LESS_THAN_INTENDED

            successRate = 0
            if g_loop_intended_total > 0:
                successRate = float(g_loop_pass) / float(g_loop_intended_total) * 100
            if successRate < g_required_pass_rate:
                remarks = remarks + REMARK_LOW_PASS_RATE

                # main_func_name = inspect.stack()[2 + functionDepth][3]
            # print "main function nane in ful summary",main_func_name
            # g_crash_text=g_logger.getCrashText(main_func_name,g_loop_Crash)
            g_crash_text = ''
            # print "crash text is",g_crash_text
            g_reporter.writeReport(LOOP_SUMMARY, SUMMARY, g_loop_intended_total, start_time, end_time, g_loop_act_total,
                                   g_loop_pass, g_loop_fail, remarks,
                                   LOOP_SUMMARY + ' for Loop - %d' % (g_loop_counter))
            g_reporter.writeMTBFReport(g_mtbf_start_time, end_time)
            g_logger.moveMenuNavigationResultImage()
            # Device_Sleep(5)
            # time.sleep(300)
            time.sleep(10)
            g_reporter.closeReportFile()
            g_reporter = None
            if None != g_logger:
                g_logger.stopLogCollection()
                g_logger = None
            util.pylogger.warn(
                '========================================== Loop - %d End ===========================================' % (
                g_loop_counter))
            util.pylogger.warn('============================= Loop - %d End time - %s =============================' % (
            g_loop_counter, str(end_time)))
            if configurator.ENABLE_UPDATE_DASHBOARD:
                end_time = util.g_last_good_device_time
                print "End time : ", end_time
                mtbfValue = end_time - start_time
                print "mtbfValue before : ", mtbfValue
                match = re.match('(\\d{2}):(\\d{2}):(\\d{2})', str(mtbfValue), re.M | re.I)
                if match:
                    mtbfValue = match.group(1)
                match = re.match('(\\d{1}):(\\d{2}):(\\d{2})', str(mtbfValue), re.M | re.I)
                if match:
                    mtbfValue = match.group(1)
                match = re.match('(\\d{3}):(\\d{2}):(\\d{2})', str(mtbfValue), re.M | re.I)
                if match:
                    mtbfValue = match.group(1)

                print "mtbfValue after : ", mtbfValue
                setupIdQuery = "UPDATE Rack_Info SET MTBF = MTBF + " + str(
                    mtbfValue) + " WHERE Build_Id LIKE '%" + g_build_id + "%' AND Device_Id LIKE '" + g_device_id + "' AND Run_Id = " + str(
                    configurator.RUN_ID) + ";"
                print "Select query for Update MTBF in Rack_Info : ", setupIdQuery
                g_db.runSQLCommand(setupIdQuery)
    except(StabilityDeviceRebootError, StabilityCommandExecutionError, StabilityDeviceTimeError), e:
        util.pylogger.warn('Reason - ' + str(e.value))
        if configurator.ENABLE_UPDATE_DASHBOARD:
            sqlquery = "UPDATE Rack_Info SET Status = " + str(
                2) + " WHERE Build_Id LIKE '%" + g_build_id + "%' AND Device_Id LIKE '" + g_device_id + "' AND Run_Id = " + str(
                configurator.RUN_ID) + ";"
            print "Update rack info running status :", sqlquery
            g_db.runSQLCommand(sqlquery)
        util.pylogger.warn(
            '===================================================================================================')
        util.pylogger.warn(
            '=============== EXCEPTION - STABILITY ABORTED;' + 'Reason - ' + str(e.value) + ' ================')
        util.pylogger.warn(
            '===================================================================================================')
        excpVal = e.value

    except(KeyboardInterrupt):
        if configurator.ENABLE_UPDATE_DASHBOARD:
            sqlquery = "UPDATE Rack_Info SET Status = " + str(
                0) + " WHERE Build_Id LIKE '%" + g_build_id + "%' AND Device_Id LIKE '" + g_device_id + "' AND Run_Id = " + str(
                configurator.RUN_ID) + ";"
            print "Update rack info running status :", sqlquery
            g_db.runSQLCommand(sqlquery)
        util.pylogger.warn(
            '===================================================================================================')
        util.pylogger.warn(
            '=========================== EXCEPTION - STABILITY INTERRUPTED BY USER =============================')
        util.pylogger.warn(
            '===================================================================================================')
        excpVal = 'INTERRUPTED BY USER'

    except:
        if configurator.ENABLE_UPDATE_DASHBOARD:
            excpVal = sys.exc_info()[0]
            sqlquery = "UPDATE Rack_Info SET Status = " + str(
                2) + " WHERE Build_Id LIKE '%" + g_build_id + "%' AND Device_Id LIKE '" + g_device_id + "' AND Run_Id = " + str(
                configurator.RUN_ID) + ";"
            print "Update rack info running status :", sqlquery
            g_db.runSQLCommand(sqlquery)
        util.pylogger.warn(
            '===================================================================================================')
        util.pylogger.warn(
            '============================= GENERAL EXCEPTION (%s) ===============================' % (excpVal))
        util.pylogger.warn(
            '===================================================================================================')
        raise

    finally:
        end_time = util.g_last_good_device_time

        if None != end_time:
            if None != g_reporter:
                remarks = REMARK_OK
                if g_loop_act_total != g_loop_intended_total:
                    remarks = remarks + REMARK_LESS_THAN_INTENDED

                successRate = 0
                if g_loop_intended_total > 0:
                    successRate = float(g_loop_pass) / float(g_loop_intended_total) * 100
                if successRate < g_required_pass_rate:
                    remarks = remarks + REMARK_LOW_PASS_RATE


                    # main_func_name = inspect.stack()[2 + functionDepth][3]
                # print "main function nane in ful summary",main_func_name
                # g_crash_text=g_logger.getCrashText(main_func_name,g_loop_Crash)
                g_crash_text = ' '
                # print "crash text is",g_crash_text

                g_reporter.writeReport(LOOP_SUMMARY, SUMMARY, g_loop_intended_total, start_time, end_time,
                                       g_loop_act_total, g_loop_pass, g_loop_fail, remarks,
                                       LOOP_SUMMARY + ' for Loop - %d' % (g_loop_counter))
                g_reporter.writeExceptionReport(excpVal)
                g_reporter.writeMTBFReport(g_mtbf_start_time, end_time)
                g_reporter.closeReportFile()
                g_reporter = None
            if None != g_logger:
                g_logger.moveMenuNavigationResultImage()
                g_logger.stopLogCollection()
                g_logger = None


def PrintDiskStats():
    strDiskStats = commands.getoutput('adb -s ' + g_device_A_id + ' shell dumpsys diskstats')
    util.pylogger.warn(strDiskStats)


def getDeviceDetails():
    global g_device_id, g_build_id, g_product_name, g_android_version, g_uptime
    print "===============================  getDeviceDetails ================================================"
    g_device_id = g_device_A_id
    g_build_id = commands.getoutput('adb -s ' + g_device_A_id + ' shell getprop ro.build.display.id')
    g_build_id = g_build_id.replace(" ", "")
    g_build_id = g_build_id.replace("\r", "")
    # print "g_build_id",g_build_id
    model = commands.getoutput('adb -s ' + g_device_A_id + ' shell getprop ro.product.model')
    model = model.replace("\r", "")
    brand = commands.getoutput('adb -s ' + g_device_A_id + ' shell getprop ro.product.brand')
    brand = brand.replace("\r", "")
    g_product_name = brand + " " + model
    setDeviceUptime()
    g_android_version = commands.getoutput('adb -s ' + g_device_A_id + ' shell getprop ro.build.version.release')
    g_android_version = g_android_version.replace("\r", "")


def setupRackInfoTable():
    global g_device_id, g_build_id, g_product_name, g_android_version, g_uptime, g_db, g_setupId, g_mtbf_start_time
    print "===============================  setupRackInfoTable ================================================"
    sqlquery = "INSERT INTO Rack_Info  (`Build_Id`,`Run_Id`, `Device_Id`,`IMEI`, `Status`, `Uptime`,`Start_Time`,`MTBF`, `Result`) VALUES ('" + str(
        g_build_id) + "'," + str(configurator.RUN_ID) + ",'" + g_device_id + "','" + "IMEI" + "','" + str(
        1) + "','" + str(g_uptime) + "','" + str(g_mtbf_start_time) + "'," + str(0) + ",'" + "1" + "');"
    print sqlquery
    g_db.runSQLCommand(sqlquery)

    setupIdQuery = "SELECT MAX(ID) FROM Rack_Info WHERE Device_Id = '" + g_device_id + "' and Build_Id LIKE '%" + g_build_id + "%';"
    print "Select query : ", setupIdQuery
    g_setupId = g_db.runSQLCommand(setupIdQuery)
    print "g_setupId =========== ", g_setupId


def setupSummaryTable():
    global g_device_id, g_build_id, g_product_name, g_android_version, g_uptime, g_db, g_setupId
    print "===============================  Start Setup Summary table ================================================"

    setupIdQuery = "SELECT Run_Id FROM Rack_Info WHERE Build_Id LIKE '%" + g_build_id + "%';"
    print "Select query for Run ID : ", setupIdQuery
    Run_id = g_db.runSQLCommand(setupIdQuery)
    print "Run_id =========== Returned value ", Run_id

    setupIdQuery = "SELECT COUNT(DISTINCT Device_Id) FROM Rack_Info WHERE Build_Id LIKE '%" + g_build_id + "%';"
    print "Select query for Setups_Count : ", setupIdQuery
    Setups_Count = g_db.runSQLCommand(setupIdQuery)
    print "Setups_Count =========== Returned value ", Setups_Count

    project_name = configurator.PROJECT_NAME

    SummaryForBuildQuery = "SELECT COUNT(*) FROM Summary WHERE Build_Id LIKE '%" + g_build_id + "%' AND Project_Name = '" + project_name + "' AND Run_Id = " + str(
        configurator.RUN_ID) + ";"
    SummaryForBuildCount = g_db.runSQLCommand(SummaryForBuildQuery)
    print "SummaryForBuildCount : ", SummaryForBuildCount
    if SummaryForBuildCount == 0:
        sqlquery = "INSERT INTO Summary (`Run_Id`,`Build_Id`,`Product_Name`,`Android_Version`,`MTBF`,`Devices_Count`,`Project_Name`,`Overall_Result`,`Description`) VALUES (" + str(
            Run_id) + ",'" + str(g_build_id) + "','" + g_product_name + "','" + g_android_version + "'," + str(
            0) + "," + str(Setups_Count) + ",'" + project_name + "'," + str(0) + ",'" + configurator.DESCRIPTION + "');"
    else:
        sqlquery = "UPDATE Summary SET Devices_Count = " + str(
            Setups_Count) + " WHERE Build_Id LIKE '%" + g_build_id + "%' AND Project_Name = '" + project_name + "';"
    print "insert command Summary before :", sqlquery
    g_db.runSQLCommand(sqlquery)
    print "insert command Summary :", sqlquery
    printBetweenLogsL2(sqlquery)

    time.sleep(2)
    VerifyRunIdQuery = "SELECT COUNT(*) FROM Summary WHERE Build_Id LIKE '%" + g_build_id + "%' AND Project_Name = '" + project_name + "' AND Run_Id = " + str(
        configurator.RUN_ID) + ";"
    RunIdCount = g_db.runSQLCommand(VerifyRunIdQuery)
    print "VerifyRunIdQuery : ", VerifyRunIdQuery
    print "RunIdCount : ", RunIdCount
    if RunIdCount == 0:
        sqlquery = "INSERT INTO Summary (`Run_Id`,`Build_Id`,`Product_Name`,`Android_Version`,`MTBF`,`Devices_Count`,`Project_Name`,`Overall_Result`,`Description`) VALUES (" + str(
            configurator.RUN_ID) + ",'" + str(
            g_build_id) + "','" + g_product_name + "','" + g_android_version + "'," + str(0) + "," + str(
            Setups_Count) + ",'" + project_name + "'," + str(0) + ",'" + configurator.DESCRIPTION + "');"
        g_db.runSQLCommand(sqlquery)


def setDeviceUptime():
    global g_device_id, g_build_id, g_product_name, g_android_version, g_uptime, g_db, g_setupId, g_mtbf_start_time
    g_uptime = commands.getoutput('adb -s ' + g_device_A_id + ' shell uptime')
    match = re.match('up time: (\\d{2}):(\\d{2}):(\\d{2})', g_uptime, re.M | re.I)
    if not g_uptime.find("day") == -1:
        # g_uptime = match.group(1)+":"+match.group(2)+":"+match.group(3)
        match1 = re.search(r'up (\d{1}) day,  (\d{1}):(\d{2})', g_uptime, re.M | re.I)
        if match1:
            number_of_hrs = (int(match1.group(1)) * 24 + int(match1.group(2)))
            g_uptime = str(number_of_hrs) + ":" + match1.group(3)
    if match:
        g_uptime = match.group(1) + ":" + match.group(2) + ":" + match.group(3)


def prepareCommand(testClass, testMethod, testPackage, testRunner, loops):
    global g_dummy_cmd
    global g_Current_testClass, g_Current_testMethod, g_Current_testPackage, g_Current_testRunner
    g_Current_testClass = testClass
    g_Current_testMethod = testMethod
    g_Current_testPackage = testPackage
    g_Current_testRunner = testRunner
    cmd = ''
    cmd = ADBCMD_2_EXTRAS % (g_device_A_id, testClass + '#' + testMethod, testPackage + '/' + testRunner)
    g_dummy_cmd = ''
    g_dummy_cmd = ADBCMD_2_EXTRAS % (
    g_device_A_id, testClass + '#' + testMethod + '123', testPackage + '/' + testRunner)
    return cmd


def updateSummaryTable():
    global g_device_id, g_build_id, g_product_name, g_android_version, g_uptime, g_db, g_setupId


def updateExecutionTable():
    global g_device_id, g_build_id, g_product_name, g_android_version, g_uptime, g_db, g_setupId


def updateRackInfoTable():
    global g_device_id, g_build_id, g_product_name, g_android_version, g_uptime, g_db, g_setupId


def PrepareUIAutomatorCmd(testClass, testMethod):
    global g_device_A_id
    global g_dummy_cmd
    global g_Current_testClass, g_Current_testMethod, g_Current_testPackage, g_Current_testRunner
    g_Current_testClass = testClass
    g_Current_testMethod = testMethod
    cmd = ''
    cmd = ADBCMD_UIAUTOMATOR % (g_device_A_id, testClass + '#' + testMethod)
    return cmd


def PrepareUIAutomator_YouStreaming_Cmd(testClass, testMethod, jarName, loops, duration):
    global g_device_A_id
    global g_dummy_cmd
    global g_Current_testClass, g_Current_testMethod, g_Current_testPackage, g_Current_testRunner
    g_Current_testClass = testClass
    g_Current_testMethod = testMethod
    cmd = ''
    cmd = ADBCMD_UIAUTOMATOR_YOUTUBE % (g_device_A_id, jarName, testClass + '#' + testMethod, duration)
    print cmd
    return cmd


def PrepareUIAutomatorCmdB_ExtraParam(testClass, testMethod, jarName, loops, extraparam):
    global g_device_A_id
    global g_dummy_cmd
    global g_Current_testClass, g_Current_testMethod, g_Current_testPackage, g_Current_testRunner
    g_Current_testClass = testClass
    g_Current_testMethod = testMethod
    ADBCMD_UIAUTOMATOR = 'adb -s %s shell uiautomator runtest %s -c %s -e ' + LOOP_COUNTER_STRING + ' ' + str(loops)
    cmd = ''
    cmd = ADBCMD_UIAUTOMATOR_EXTRA % (g_device_B_id, jarName, testClass + '#' + testMethod, extraparam)
    cmd = string.replace(cmd, 'xxx', str(loops))
    return cmd


def PrepareUIAutomatorCmdnoloop(testClass, testMethod, jarName):
    global g_device_A_id
    global g_dummy_cmd
    global g_Current_testClass, g_Current_testMethod, g_Current_testPackage, g_Current_testRunner
    g_Current_testClass = testClass
    g_Current_testMethod = testMethod
    cmd = ''
    cmd = ADBCMD_UIAUTOMATOR_NO_LOOP % (g_device_A_id, jarName, testClass + '#' + testMethod)
    return cmd


def prepareCommandNoLoop(testClass, testMethod, testPackage, testRunner):
    cmd = ''
    cmd = ADBCMD_1_EXTRA % (g_device_A_id, testClass + '#' + testMethod, testPackage + '/' + testRunner)
    return cmd


def prepareCommandNoLoopPhoneB(testClass, testMethod, testPackage, testRunner):
    cmd = ''
    cmd = ADBCMD_1_EXTRA % (g_device_B_id, testClass + '#' + testMethod, testPackage + '/' + testRunner)
    return cmd


def PrepareUIAutomatorCmdB(testClass, testMethod, jarName, loops):
    global g_device_A_id
    global g_dummy_cmd
    global g_Current_testClass, g_Current_testMethod, g_Current_testPackage, g_Current_testRunner
    g_Current_testClass = testClass
    g_Current_testMethod = testMethod
    ADBCMD_UIAUTOMATOR = 'adb -s %s shell uiautomator runtest %s -c %s -e ' + LOOP_COUNTER_STRING + ' ' + str(loops)
    cmd = ''
    cmd = ADBCMD_UIAUTOMATOR % (g_device_B_id, jarName, testClass + '#' + testMethod)
    return cmd


def printBeginLogsL1(functionDepth=0):
    starter = '>>> ' + '{Loop - %d}' % (g_loop_counter) + '[' + inspect.stack()[1 + functionDepth][
        3] + '] ' + '- Begin '
    filler = '>' * (90 - len(starter) - 1)
    util.pylogger.warn('\n' + starter + filler)


def printBetweenLogsL1(log, functionDepth=0):
    costStr = '{Loop - %d}' % (g_loop_counter) + '[' + inspect.stack()[1 + functionDepth][3] + '] - '
    starter = '--- ' + costStr
    util.pylogger.warn(starter + log)


def printEndLogsL1(functionDepth=0):
    starter = '<<< ' + '{Loop - %d}' % (g_loop_counter) + '[' + inspect.stack()[1 + functionDepth][3] + '] ' + '- End '
    filler = '<' * (90 - len(starter) - 1)
    util.pylogger.warn(starter + filler + '\n')


def printBeginLogsL2(functionDepth=0):
    starter = '>>> ' + '{Loop - %d}' % (g_loop_counter) + '[' + inspect.stack()[3 + functionDepth][3] + ']' + '(' + \
              inspect.stack()[2 + functionDepth][3] + ') ' + '- Begin '
    filler = '>' * (78 - len(starter) - 1)
    util.pylogger.warn('\n' + starter + filler)


def printBetweenLogsL2(log, functionDepth=0):
    constStr = '{Loop - %d}' % (g_loop_counter) + '[' + inspect.stack()[3 + functionDepth][3] + ']' + '(' + \
               inspect.stack()[2 + functionDepth][3] + ') - '
    starter = '--- ' + constStr
    util.pylogger.warn(starter + log)


def printEndLogsL2(functionDepth=0):
    starter = '<<< ' + '{Loop - %d}' % (g_loop_counter) + '[' + inspect.stack()[3 + functionDepth][3] + ']' + '(' + \
              inspect.stack()[2 + functionDepth][3] + ') ' + '- End '
    filler = '<' * (78 - len(starter) - 1)
    util.pylogger.warn(starter + filler + '\n')


def captureDeviceErrorData(fileScreenShot, fileBugReport):
    devID = g_device_A_id
    commands.getoutput('adb -s ' + devID + ' root')
    commands.getoutput('adb -s ' + devID + ' remount')


def executeWaitAndReport(cmd, intendedLoops, sleepTime, functionDepth=0, dummyCmd=''):
    global g_to_be_retried, g_remaining_loop_count, g_logger
    g_to_be_retried = False
    functionDepth = functionDepth + 1
    # print cmd
    newCommand = string.replace(cmd, 'xxx', str(intendedLoops))
    print newCommand
    executeWaitAndReportActual(newCommand, intendedLoops, sleepTime, functionDepth)
    if True == g_to_be_retried:
        # newCommand = prepareCommand(g_Current_testClass, g_Current_testMethod, g_Current_testPackage, g_Current_testRunner, g_remaining_loop_count)
        newCommand = string.replace(cmd, 'xxx', str(g_remaining_loop_count))
        executeWaitAndReportActual(newCommand, g_remaining_loop_count, sleepTime, functionDepth)
        g_to_be_retried = False
        g_remaining_loop_count = 0


def executeUIAutomatorWaitAndReport(cmd, intendedLoops, sleepTime, functionDepth=0, dummyCmd=''):
    global g_to_be_retried, g_remaining_loop_count, g_logger
    g_to_be_retried = False
    functionDepth = functionDepth + 1
    executeWaitAndReportActual(cmd, intendedLoops, sleepTime, functionDepth)
    if True == g_to_be_retried:
        newCommand = PrepareUIAutomatorCmd(g_Current_testClass, g_Current_testMethod, g_jarName, g_remaining_loop_count)
        executeWaitAndReportActual(newCommand, g_remaining_loop_count, sleepTime, functionDepth)
        g_to_be_retried = False
        g_remaining_loop_count = 0


g_Is_Specialcase_Retry = False


def executeWaitAndReportActual(cmd, intendedLoops, sleepTime, functionDepth=0, dummyCmd=''):
    global g_loop_intended_total, g_loop_act_total, g_loop_pass, g_loop_fail, g_remaining_loop_count
    global g_testcase_intended_total, g_testcase_act_total, g_testcase_pass, g_testcase_fail, g_dummy_cmd, g_to_be_retried
    global g_logger, g_Total_Pass, g_db, g_setupId, g_collect_bugreport
    global g_Is_Specialcase_Retry, g_tempCount, g_total_crashcount, g_crash_text

    # Gets Test Component Name
    main_func_name = inspect.stack()[2 + functionDepth][3]
    # Gets Test Case Name
    sub_func_name = inspect.stack()[1 + functionDepth][3]
    g_logger.collectMemInfoExtended(main_func_name, sub_func_name)
    g_logger.collectBatteryInfoExtended(main_func_name, sub_func_name)

    start_time = getDeviceCurrentTime()
    bDeviceReset = False

    printBeginLogsL2(functionDepth)
    printBetweenLogsL2('Start time - ' + str(start_time), functionDepth)
    PrintDiskStats()
    if intendedLoops > 0:
        printBetweenLogsL2('Intend to run %d loops' % (intendedLoops), functionDepth)
    else:
        printBetweenLogsL2('This is a preparatory step', functionDepth)

    executor = testexecutor.TestExecutor(g_device_A_id)
    retVal = executor.execute(cmd, intendedLoops)
    remarks = ''

    if True == g_to_be_retried:
        remarks = remarks + REMARK_DEVICE_RETRY

    if common.ERROR_NO_ERROR == retVal:
        printBetweenLogsL2('Completed. Continuing...', functionDepth)
        remarks = remarks + REMARK_OK
    elif common.ERROR_NON_FATAL == retVal:
        if executor.capture_device_data:
            err_screen_file_name = util.getLoopOutputPath(g_loop_counter) + '/ScreenCapture_' + sub_func_name
            err_bugreport_file_name = util.getLoopOutputPath(g_loop_counter) + '/bugreport_' + sub_func_name
            captureDeviceErrorData(err_screen_file_name, err_bugreport_file_name)
        printBetweenLogsL2('Some tests are INCOMPLETE. Continuing...', functionDepth)
        if len(executor.anr_or_fc_error) > 0:
            remarks = remarks + REMARK_NON_FATAL_ANR_OR_FC
        else:
            if True == checkDeviceReboot():
                remarks = remarks + REMARK_DEVICE_RESET
                bDeviceReset = True
            else:
                remarks = remarks + REMARK_NON_FATAL
                remarks = remarks + REMARK_DEVICE_DISCONNECTED_RETRY
                g_remaining_loop_count = intendedLoops - (
                executor.total_pass + executor.total_fail + executor.total_error)
                if g_dummy_cmd.find('CallB') == -1 or g_dummy_cmd.find('CalllogB') == -1:
                    executor.stopCurrentExecution(g_dummy_cmd)
                else:
                    g_dummy_cmd = ''
                    printBetweenLogsL2(
                        'skip running dummy testcase like <testcase>123 function to kill existing running test for Telephony')
                g_to_be_retried = True
                g_logger.stopLogCollection()
                g_logger.collectLogs(main_func_name + '_Retry')

        print 'ERROR_NON_FATAL so Stopping.....'
        if len(g_dummy_cmd) > 0:
            executor.stopCurrentExecution(g_dummy_cmd)
            g_dummy_cmd = ''

    elif common.ERROR_FATAL == retVal:
        if executor.capture_device_data:
            err_screen_file_name = util.getLoopOutputPath(g_loop_counter) + '/ScreenCapture_' + sub_func_name
            err_bugreport_file_name = util.getLoopOutputPath(g_loop_counter) + '/bugreport_' + sub_func_name
            captureDeviceErrorData(err_screen_file_name, err_bugreport_file_name)
        printBetweenLogsL2('ABORTING due to fatal error...', functionDepth)
        remarks = remarks + REMARK_FATAL
        print 'ERROR_FATAL so Stopping.....'
        if len(g_dummy_cmd) > 0:
            executor.stopCurrentExecution(g_dummy_cmd)
            g_dummy_cmd = ''

    current_time = getDeviceCurrentTime()
    printBetweenLogsL2('Execution completed - ' + str(current_time) + '. Now waiting...', functionDepth)
    time.sleep(sleepTime)

    end_time = getDeviceCurrentTime()
    printBetweenLogsL2('End time - ' + str(end_time), functionDepth)
    printBetweenLogsL2('Status - ' + executor.status, functionDepth)
    printBetweenLogsL2('Duration - ' + str(end_time - start_time), functionDepth)
    ##Getting crash count
    # print "main function name is",main_func_name
    g_total_crashcount = g_logger.getCrashCount(main_func_name)
    # print "g_total_crashcount is",g_total_crashcount
    crash_current = int(g_total_crashcount) - int(g_tempCount)
    g_crash_text = g_logger.getCrashText(main_func_name, crash_current)
    # print "crash text is",g_crash_text
    g_tempCount = int(g_total_crashcount)

    # print "g_tempcount",g_tempCount
    # print "crash_current",crash_current
    # print "g_total_crashcount",g_total_crashcount

    ##calculating current crash count
    if intendedLoops > 0:
        printBetweenLogsL2('Total pass - ' + str(executor.total_pass) + '; Pass list - ' + ''.join(
            ["%s," % el for el in executor.pass_list]), functionDepth)
        printBetweenLogsL2('Total fail - ' + str(executor.total_fail) + '; Fail list - ' + ''.join(
            ["%s," % el for el in executor.fail_list]), functionDepth)
        printBetweenLogsL2('Total error - ' + str(executor.total_error) + '; Error list - ' + ''.join(
            ["%s," % el for el in executor.error_list]), functionDepth)
        g_Total_Pass = 0
        testTotal = executor.total_pass + executor.total_fail + executor.total_error
        testPass = executor.total_pass
        g_Total_Pass = testPass
        testFail = executor.total_fail + executor.total_error  # Errors are failures

        if testTotal != intendedLoops:
            remarks = remarks + REMARK_LESS_THAN_INTENDED

        successRate = 0
        if intendedLoops > 0:
            successRate = float(testPass) / float(intendedLoops) * 100
        if successRate < g_required_pass_rate:
            remarks = remarks + REMARK_LOW_PASS_RATE

        g_reporter.writeReport(inspect.stack()[2 + functionDepth][3], inspect.stack()[1 + functionDepth][3],
                               intendedLoops, start_time, end_time, testTotal, testPass, testFail, remarks,
                               executor.getDetails())

        g_testcase_intended_total = g_testcase_intended_total + intendedLoops
        g_testcase_act_total = g_testcase_act_total + testTotal
        g_testcase_pass = g_testcase_pass + testPass
        g_testcase_fail = g_testcase_fail + testFail

        g_loop_intended_total = g_loop_intended_total + intendedLoops
        g_loop_act_total = g_loop_act_total + testTotal
        g_loop_pass = g_loop_pass + testPass
        g_loop_fail = g_loop_fail + testFail
        print "Setup id in executor ", g_setupId
        if configurator.ENABLE_UPDATE_DASHBOARD:
            if g_Is_Specialcase_Retry == False:
                sqlquery = "INSERT INTO Execution  (`ID`,`Loop`, `Component_Name`, `Testcase`, `Attempts`, `Pass`, `Fail`, `Start_Time`, `End_Time`) VALUES (" + str(
                    g_setupId) + "," + str(g_loop_counter) + ",'" + inspect.stack()[2 + functionDepth][3] + "','" + \
                           inspect.stack()[1 + functionDepth][3] + "'," + str(intendedLoops) + "," + str(
                    testPass) + "," + str(testFail) + ",'" + str(start_time) + "','" + str(end_time) + "');"
            else:
                sqlquery = "UPDATE Execution SET Pass=" + str(testPass) + ",Fail=" + str(
                    testFail) + ",Start_Time='" + str(start_time) + "',End_Time='" + str(
                    end_time) + "' WHERE  Testcase='" + inspect.stack()[1 + functionDepth][3] + "' AND `Loop`=" + str(
                    g_loop_counter) + " AND ID=" + str(g_setupId) + ";"
            print sqlquery
            g_db.runSQLCommand(sqlquery)

        setDeviceUptime()
        if configurator.ENABLE_UPDATE_DASHBOARD:
            updateUptimeQuery = "UPDATE Rack_Info SET Uptime = '" + str(
                g_uptime) + "' WHERE Build_Id LIKE '%" + g_build_id + "%' AND Device_Id LIKE '" + g_device_id + "' AND Run_Id = " + str(
                configurator.RUN_ID) + ";"

            print "Select query for Update MTBF in Rack_Info : ", updateUptimeQuery
            g_db.runSQLCommand(updateUptimeQuery)

            print 'After fun call'
    else:  # Non test report
        g_reporter.writeNonTestReport(inspect.stack()[2 + functionDepth][3], inspect.stack()[1 + functionDepth][3],
                                      start_time, end_time)

    printEndLogsL2(functionDepth)

    if common.ERROR_FATAL == retVal:
        if None != g_logger:
            g_logger.stopLogCollection()
        exception = StabilityCommandExecutionError(executor.fatal_error)
        raise exception
    if True == bDeviceReset:
        if None != g_logger:
            g_logger.stopLogCollection()
        exception = StabilityDeviceRebootError(REMARK_DEVICE_RESET)
        raise exception
    g_logger.take_Screenshot(inspect.stack()[1 + functionDepth][3], g_collect_bugreport)


def executeThreadOnPhone(cmd, intendedLoops, sleepTime, device_id):
    executorPhoneB = testexecutor.TestExecutor(device_id)
    executorPhoneB.executeThreadOnPhone(cmd, intendedLoops)
    time.sleep(sleepTime)


def getDeviceCurrentTime():
    retVal = util.getDeviceTime()
    if retVal == None:
        counter = 0
        while counter < common.DEVICE_CHECK_COUNTER:  # Wait for 120 seconds for device to connect over ADB
            time.sleep(common.DEVICE_CHECK_TIMEOUT)
            util.pylogger.warn('getDeviceCurrentTime - Retrying... - %d' % (counter + 1))
            retVal = util.getDeviceTime()
            if retVal != None:
                util.pylogger.warn('getDeviceCurrentTime -Got device time')
                util.pylogger.warn('Checking if device has rebooted...')
                if True == checkDeviceReboot():
                    util.pylogger.warn('@@@ FATAL ERROR @@@ Device has rebooted')
                    if None != g_logger:
                        g_logger.stopLogCollection()
                    exception = StabilityDeviceRebootError(REMARK_DEVICE_RESET)
                    raise exception
                else:
                    break
            counter = counter + 1

    if retVal == None:
        if None != g_logger:
            g_logger.stopLogCollection()
        exception = StabilityDeviceTimeError(
            common.FATAL_ERROR_ADB_CONNECTION_LOST_1 + ' or ' + common.FATAL_ERROR_ADB_CONNECTION_LOST_2)
        raise exception

    return retVal


def checkDeviceReboot():
    time.sleep(30)

    device_start_time = util.getDeviceStartTime()
    if g_device_start_time != device_start_time:
        util.pylogger.warn('@@@ FATAL ERROR @@@ - Device has rebooted')
        util.pylogger.warn('Original Start Time - %s' % (str(g_device_start_time)))
        util.pylogger.warn('Current Start Time - %s' % (str(device_start_time)))
        return True
    util.pylogger.warn('Device has NOT rebooted')
    return False


# ============= 5.1.1 TELEPHONY ===============
def Telephony():
    global g_logger, g_tempCount, g_total_crashcount, g_loop_Crash, g_loop_counter, g_crash_text
    g_tempCount = 0
    g_crash_text = ''

    printBeginLogsL1()
    g_logger.collectLogs(Telephony.func_name)
    g_logger.collectPhoneBLogs(Telephony.func_name)

    start_time = getDeviceCurrentTime()
    printBetweenLogsL1('Starting tests...')
    printBetweenLogsL1('Start Time = ' + str(start_time))

    Add_Contact()
    Delete_Contact()

    g_loop_Crash = int(g_loop_Crash) + int(g_total_crashcount)
    end_time = getDeviceCurrentTime()
    printBetweenLogsL1('Done')
    printBetweenLogsL1('End Time = ' + str(end_time))
    printBetweenLogsL1('Duration - ' + str(end_time - start_time))
    printBetweenLogsL1('Intended total - ' + str(g_testcase_intended_total))
    printBetweenLogsL1('Actual total - ' + str(g_testcase_act_total))
    printBetweenLogsL1('Actual passed - ' + str(g_testcase_pass))
    printBetweenLogsL1('Actual failures - ' + str(g_testcase_fail))

    g_logger.stopPhoneBLogCollection()
    g_logger.stopLogCollection(Telephony.func_name)
    g_logger.Clear_Logs_sdcard()

    remarks = REMARK_OK
    if g_testcase_act_total != g_testcase_intended_total:
        remarks = remarks + REMARK_LESS_THAN_INTENDED
    successRate = 0
    if g_testcase_intended_total > 0:
        successRate = float(g_testcase_pass) / float(g_testcase_intended_total) * 100
    if successRate < g_required_pass_rate:
        remarks = remarks + REMARK_LOW_PASS_RATE

    g_crash_text = g_logger.getCrashText(Telephony.func_name, g_tempCount)
    # print "crash text is",g_crash_text
    g_reporter.writeReport(inspect.stack()[0][3], SUMMARY, g_testcase_intended_total, start_time, end_time,
                           g_testcase_act_total, g_testcase_pass, g_testcase_fail, remarks, SUMMARY)

    util.removeScreenShotFolder(g_loop_counter)

    printEndLogsL1()
    if g_kill_processes == True:
        g_logger.CleanUpProcesses()
    if g_kill_All_Apps == True:
        util.KillAllApps()


def Add_Contact():
    intendedLoops = configurator.TELEPHONY_ADD_CONTACT_COUNTER
    cmd = PrepareUIAutomatorCmd('borqs.test.ContactTest', 'testAddContact', 'mtbf.jar', intendedLoops)
    executeWaitAndReport(cmd, intendedLoops, INTERVAL_TIME)


def Delete_Contact():
    intendedLoops = configurator.TELEPHONY_DELETE_CONTACT_COUNTER
    cmd = PrepareUIAutomatorCmd('borqs.test.ContactTest', 'testDeleteContact', 'mtbf.jar', intendedLoops)
    executeWaitAndReport(cmd, intendedLoops, INTERVAL_TIME)


def Device_Sleep(delayInMin):
    intendedLoops = delayInMin
    cmd = prepareCommand('borqs.stabilitytest.settings.MenuNavTest', 'testDeviceSleep', 'borqs.stabilitytest.settings',
                         '.AT_ST_Settings_TestRunner', intendedLoops)
    executeWaitAndReport(cmd, intendedLoops, INTERVAL_TIME)


# ============= 5.1.3 EMAIL ===============
def Email():
    global g_logger, g_tempCount, g_total_crashcount, g_loop_Crash, g_loop_counter, g_crash_text
    g_tempCount = 0
    printBeginLogsL1()
    g_logger.collectLogs(Email.func_name)

    start_time = getDeviceCurrentTime()
    printBetweenLogsL1('Starting tests...')
    printBetweenLogsL1('Start Time = ' + str(start_time))

    Switch3G()
    Send_No_Attachment_3G()
    Send_With_Attachment_3G()
    SwitchLTE()
    Send_No_Attachment_LTE()
    Send_With_Attachment_LTE()
    Open_Email()

    g_loop_Crash = int(g_loop_Crash) + int(g_total_crashcount)
    end_time = getDeviceCurrentTime()
    printBetweenLogsL1('Done')
    printBetweenLogsL1('End Time = ' + str(end_time))
    printBetweenLogsL1('Duration - ' + str(end_time - start_time))
    printBetweenLogsL1('Intended total - ' + str(g_testcase_intended_total))
    printBetweenLogsL1('Actual total - ' + str(g_testcase_act_total))
    printBetweenLogsL1('Actual passed - ' + str(g_testcase_pass))
    printBetweenLogsL1('Actual failures - ' + str(g_testcase_fail))

    g_logger.stopLogCollection(Email.func_name)
    g_logger.Clear_Logs_sdcard()
    remarks = REMARK_OK
    if g_testcase_act_total != g_testcase_intended_total:
        remarks = remarks + REMARK_LESS_THAN_INTENDED

    successRate = 0
    if g_testcase_intended_total > 0:
        successRate = float(g_testcase_pass) / float(g_testcase_intended_total) * 100
    if successRate < g_required_pass_rate:
        remarks = remarks + REMARK_LOW_PASS_RATE
    g_crash_text = g_logger.getCrashText(Email.func_name, g_tempCount)
    # print "crash text is",g_crash_text
    g_reporter.writeReport(inspect.stack()[0][3], SUMMARY, g_testcase_intended_total, start_time, end_time,
                           g_testcase_act_total, g_testcase_pass, g_testcase_fail, remarks, SUMMARY)

    util.removeScreenShotFolder(g_loop_counter)

    printEndLogsL1()
    if g_kill_processes == True:
        g_logger.CleanUpProcesses()
    if g_kill_All_Apps == True:
        util.KillAllApps()


def Switch3G():
    intendedLoops = 1
    cmd = PrepareUIAutomatorCmd('borqs.test.SettingsTest', 'testSwitch_3G', 'mtbf.jar', intendedLoops)
    executeWaitAndReport(cmd, intendedLoops, INTERVAL_TIME)


def SwitchLTE():
    intendedLoops = 1
    cmd = PrepareUIAutomatorCmd('borqs.test.SettingsTest', 'testSwitch_LTE', 'mtbf.jar', intendedLoops)
    executeWaitAndReport(cmd, intendedLoops, INTERVAL_TIME)


def Send_No_Attachment_3G():
    intendedLoops = configurator.EMAIL_SEND_NO_ATTACHMENT_3G_COUNTER
    cmd = PrepareUIAutomatorCmd('borqs.test.GmailTest', 'testSendGmail', 'mtbf.jar', intendedLoops)
    executeWaitAndReport(cmd, intendedLoops, INTERVAL_TIME)


def Send_No_Attachment_LTE():
    intendedLoops = configurator.EMAIL_SEND_NO_ATTACHMENT_LTE_COUNTER
    cmd = PrepareUIAutomatorCmd('borqs.test.GmailTest', 'testSendGmail', 'mtbf.jar', intendedLoops)
    executeWaitAndReport(cmd, intendedLoops, INTERVAL_TIME)


def Send_With_Attachment_3G():
    intendedLoops = configurator.EMAIL_SEND_WITH_ATTACHMENT_3G_COUNTER
    cmd = PrepareUIAutomatorCmd('borqs.test.GmailTest', 'testSendGmailWithAttachment', 'mtbf.jar', intendedLoops)
    executeWaitAndReport(cmd, intendedLoops, INTERVAL_TIME)


def Send_With_Attachment_LTE():
    intendedLoops = configurator.EMAIL_SEND_WITH_ATTACHMENT_LTE_COUNTER
    cmd = PrepareUIAutomatorCmd('borqs.test.GmailTest', 'testSendGmailWithAttachment', 'mtbf.jar', intendedLoops)
    executeWaitAndReport(cmd, intendedLoops, INTERVAL_TIME)


def Open_Email():
    intendedLoops = configurator.EMAIL_OPEN_MAIL_COUNTER
    cmd = PrepareUIAutomatorCmd('borqs.test.GmailTest', 'testOpenGmail', 'mtbf.jar', intendedLoops)
    executeWaitAndReport(cmd, intendedLoops, INTERVAL_TIME)


# ============= 5.1.5 BROWSER ==============
def Browser():
    global g_logger, g_tempCount, g_total_crashcount, g_loop_Crash, g_loop_counter, g_crash_text
    g_tempCount = 0
    g_crash_text = ''
    printBeginLogsL1()
    g_logger.collectLogs(Browser.func_name)

    start_time = getDeviceCurrentTime()
    printBetweenLogsL1('Starting tests...')
    printBetweenLogsL1('Start Time = ' + str(start_time))

    Switch3G()
    Load_HomePage_3G()
    Launch_Link_3G()
    Load_Top_Sites_3G()
    SwitchLTE()
    Load_HomePage_LTE()
    Launch_Link_LTE()
    Load_Top_Sites_LTE()

    g_loop_Crash = int(g_loop_Crash) + int(g_total_crashcount)
    end_time = getDeviceCurrentTime()
    printBetweenLogsL1('Done')
    printBetweenLogsL1('End Time = ' + str(end_time))
    printBetweenLogsL1('Duration - ' + str(end_time - start_time))
    printBetweenLogsL1('Intended total - ' + str(g_testcase_intended_total))
    printBetweenLogsL1('Actual total - ' + str(g_testcase_act_total))
    printBetweenLogsL1('Actual passed - ' + str(g_testcase_pass))
    printBetweenLogsL1('Actual failures - ' + str(g_testcase_fail))

    g_logger.stopLogCollection(Browser.func_name)
    g_logger.Clear_Logs_sdcard()
    remarks = REMARK_OK
    if g_testcase_act_total != g_testcase_intended_total:
        remarks = remarks + REMARK_LESS_THAN_INTENDED

    successRate = 0
    if g_testcase_intended_total > 0:
        successRate = float(g_testcase_pass) / float(g_testcase_intended_total) * 100
    if successRate < g_required_pass_rate:
        remarks = remarks + REMARK_LOW_PASS_RATE

    g_crash_text = g_logger.getCrashText(Browser.func_name, g_tempCount)
    # print "crash text is",g_crash_text
    g_reporter.writeReport(inspect.stack()[0][3], SUMMARY, g_testcase_intended_total, start_time, end_time,
                           g_testcase_act_total, g_testcase_pass, g_testcase_fail, remarks, SUMMARY)

    util.removeScreenShotFolder(g_loop_counter)

    printEndLogsL1()
    if g_kill_processes == True:
        g_logger.CleanUpProcesses()
    if g_kill_All_Apps == True:
        util.KillAllApps()


def Switch3G():
    intendedLoops = 1
    cmd = PrepareUIAutomatorCmd('borqs.test.SettingsTest', 'testSwitch_3G', 'mtbf.jar', intendedLoops)
    executeWaitAndReport(cmd, intendedLoops, INTERVAL_TIME)


def SwitchLTE():
    intendedLoops = 1
    cmd = PrepareUIAutomatorCmd('borqs.test.SettingsTest', 'testSwitch_LTE', 'mtbf.jar', intendedLoops)
    executeWaitAndReport(cmd, intendedLoops, INTERVAL_TIME)


def AddBookmarks():
    intendedLoops = configurator.BROWSER_LAUNCH_HOMEPAGE_3G_COUNTER
    cmd = PrepareUIAutomatorCmd('borqs.test.BrowserTest', 'AddBookmarks', 'mtbf.jar', intendedLoops)
    executeWaitAndReport(cmd, intendedLoops, INTERVAL_TIME)


def Load_HomePage_3G():
    intendedLoops = configurator.BROWSER_LAUNCH_HOMEPAGE_3G_COUNTER
    cmd = PrepareUIAutomatorCmd('borqs.test.BrowserTest', 'testBrowserHomePage', 'mtbf.jar', intendedLoops)
    executeWaitAndReport(cmd, intendedLoops, INTERVAL_TIME)


def Launch_Link_3G():
    intendedLoops = configurator.BROWSER_OPEN_LINKS_3G_COUNTER
    cmd = PrepareUIAutomatorCmd('borqs.test.BrowserTest', 'testBrowserLinktoLink', 'mtbf.jar', intendedLoops)
    executeWaitAndReport(cmd, intendedLoops, INTERVAL_TIME)


def Load_Top_Sites_3G():
    intendedLoops = configurator.BROWSER_LOAD_TOPSITES_3G_COUNTER
    cmd = PrepareUIAutomatorCmd('borqs.test.BrowserTest', 'testBrowserTopPage', 'mtbf.jar', intendedLoops)
    executeWaitAndReport(cmd, intendedLoops, INTERVAL_TIME)


def Load_HomePage_LTE():
    intendedLoops = configurator.BROWSER_LAUNCH_HOMEPAGE_LTE_COUNTER
    cmd = PrepareUIAutomatorCmd('borqs.test.BrowserTest', 'testBrowserHomePage', 'mtbf.jar', intendedLoops)
    executeWaitAndReport(cmd, intendedLoops, INTERVAL_TIME)


def Launch_Link_LTE():
    intendedLoops = configurator.BROWSER_OPEN_LINKS_LTE_COUNTER
    cmd = PrepareUIAutomatorCmd('borqs.test.BrowserTest', 'testBrowserLinktoLink', 'mtbf.jar', intendedLoops)
    executeWaitAndReport(cmd, intendedLoops, INTERVAL_TIME)


def Load_Top_Sites_LTE():
    intendedLoops = configurator.BROWSER_LOAD_TOPSITES_LTE_COUNTER
    cmd = PrepareUIAutomatorCmd('borqs.test.BrowserTest', 'testBrowserTopPage', 'mtbf.jar', intendedLoops)
    executeWaitAndReport(cmd, intendedLoops, INTERVAL_TIME)


# ============= 5.1.5 Storefront ===============
def StoreFront():
    global g_logger, g_tempCount, g_total_crashcount, g_loop_Crash, g_loop_counter, g_crash_text
    g_tempCount = 0
    g_crash_text = ''
    printBeginLogsL1()
    g_logger.collectLogs(StoreFront.func_name)

    start_time = getDeviceCurrentTime()
    printBetweenLogsL1('Starting tests...')
    printBetweenLogsL1('Start Time = ' + str(start_time))

    Open_Close_Play()
    Switch3G()
    Download_App_3G()
    Download_Game_3G()
    SwitchLTE()
    Download_Game_LTE()
    Download_App_LTE()

    g_loop_Crash = int(g_loop_Crash) + int(g_total_crashcount)
    end_time = getDeviceCurrentTime()
    printBetweenLogsL1('Done')
    printBetweenLogsL1('End Time = ' + str(end_time))
    printBetweenLogsL1('Duration - ' + str(end_time - start_time))
    printBetweenLogsL1('Intended total - ' + str(g_testcase_intended_total))
    printBetweenLogsL1('Actual total - ' + str(g_testcase_act_total))
    printBetweenLogsL1('Actual passed - ' + str(g_testcase_pass))
    printBetweenLogsL1('Actual failures - ' + str(g_testcase_fail))

    g_logger.stopLogCollection(StoreFront.func_name)
    g_logger.Clear_Logs_sdcard()
    remarks = REMARK_OK
    if g_testcase_act_total != g_testcase_intended_total:
        remarks = remarks + REMARK_LESS_THAN_INTENDED

    successRate = 0
    if g_testcase_intended_total > 0:
        successRate = float(g_testcase_pass) / float(g_testcase_intended_total) * 100
    if successRate < g_required_pass_rate:
        remarks = remarks + REMARK_LOW_PASS_RATE

    g_crash_text = g_logger.getCrashText(StoreFront.func_name, g_tempCount)
    # print "crash text is",g_crash_text
    g_reporter.writeReport(inspect.stack()[0][3], SUMMARY, g_testcase_intended_total, start_time, end_time,
                           g_testcase_act_total, g_testcase_pass, g_testcase_fail, remarks, SUMMARY)

    util.removeScreenShotFolder(g_loop_counter)

    printEndLogsL1()
    if g_kill_processes == True:
        g_logger.CleanUpProcesses()
    if g_kill_All_Apps == True:
        util.KillAllApps()


def Switch3G():
    intendedLoops = 1
    cmd = PrepareUIAutomatorCmd('borqs.test.SettingsTest', 'testSwitch_3G', 'mtbf.jar', intendedLoops)
    executeWaitAndReport(cmd, intendedLoops, INTERVAL_TIME)


def SwitchLTE():
    intendedLoops = 1
    cmd = PrepareUIAutomatorCmd('borqs.test.SettingsTest', 'testSwitch_LTE', 'mtbf.jar', intendedLoops)
    executeWaitAndReport(cmd, intendedLoops, INTERVAL_TIME)


def Open_Close_Play():
    intendedLoops = configurator.STOREFRONT_LAUNCH_COUNTER
    cmd = PrepareUIAutomatorCmd('borqs.test.PlaystoreTest', 'testLauchPlayStore', 'mtbf.jar', intendedLoops)
    executeWaitAndReport(cmd, intendedLoops, INTERVAL_TIME)


def Download_Game_3G():
    intendedLoops = configurator.STOREFRONT_DOWNLOAD_GAME_3G_COUNTER
    cmd = PrepareUIAutomatorCmd('borqs.test.PlaystoreTest', 'testDownloadGame', 'mtbf.jar', intendedLoops)
    executeWaitAndReport(cmd, intendedLoops, INTERVAL_TIME)


def Download_App_3G():
    intendedLoops = configurator.STOREFRONT_DOWNLOAD_APP_3G_COUNTER
    cmd = PrepareUIAutomatorCmd('borqs.test.PlaystoreTest', 'testDownloadApp', 'mtbf.jar', intendedLoops)
    executeWaitAndReport(cmd, intendedLoops, INTERVAL_TIME)


def Download_Game_LTE():
    intendedLoops = configurator.STOREFRONT_DOWNLOAD_GAME_LTE_COUNTER
    cmd = PrepareUIAutomatorCmd('borqs.test.PlaystoreTest', 'testDownloadGame', 'mtbf.jar', intendedLoops)
    executeWaitAndReport(cmd, intendedLoops, INTERVAL_TIME)


def Download_App_LTE():
    intendedLoops = configurator.STOREFRONT_DOWNLOAD_APP_LTE_COUNTER
    cmd = PrepareUIAutomatorCmd('borqs.test.PlaystoreTest', 'testDownloadApp', 'mtbf.jar', intendedLoops)
    executeWaitAndReport(cmd, intendedLoops, INTERVAL_TIME)


# ============= 5.1.7 PIM ===============
def PIM():
    global g_logger, g_tempCount, g_total_crashcount, g_loop_Crash, g_loop_counter, g_crash_text
    g_tempCount = 0
    g_crash_text = ''
    printBeginLogsL1()
    g_logger.collectLogs(PIM.func_name)

    start_time = getDeviceCurrentTime()
    printBetweenLogsL1('Starting tests...')
    printBetweenLogsL1('Start Time = ' + str(start_time))

    Add_Appointment()
    Add_Alarm()
    Delete_Appointment()
    Delete_Alarm()

    g_loop_Crash = int(g_loop_Crash) + int(g_total_crashcount)
    end_time = getDeviceCurrentTime()
    printBetweenLogsL1('Done')
    printBetweenLogsL1('End Time = ' + str(end_time))
    printBetweenLogsL1('Duration - ' + str(end_time - start_time))
    printBetweenLogsL1('Intended total - ' + str(g_testcase_intended_total))
    printBetweenLogsL1('Actual total - ' + str(g_testcase_act_total))
    printBetweenLogsL1('Actual passed - ' + str(g_testcase_pass))
    printBetweenLogsL1('Actual failures - ' + str(g_testcase_fail))

    g_logger.stopLogCollection(PIM.func_name)
    g_logger.Clear_Logs_sdcard()
    remarks = REMARK_OK
    if g_testcase_act_total != g_testcase_intended_total:
        remarks = remarks + REMARK_LESS_THAN_INTENDED

    successRate = 0
    if g_testcase_intended_total > 0:
        successRate = float(g_testcase_pass) / float(g_testcase_intended_total) * 100
    if successRate < g_required_pass_rate:
        remarks = remarks + REMARK_LOW_PASS_RATE
    g_crash_text = g_logger.getCrashText(PIM.func_name, g_tempCount)
    # print "crash text is",g_crash_text
    g_reporter.writeReport(inspect.stack()[0][3], SUMMARY, g_testcase_intended_total, start_time, end_time,
                           g_testcase_act_total, g_testcase_pass, g_testcase_fail, remarks, SUMMARY)

    util.removeScreenShotFolder(g_loop_counter)

    printEndLogsL1()
    if g_kill_processes == True:
        g_logger.CleanUpProcesses()
    if g_kill_All_Apps == True:
        util.KillAllApps()


def Add_Appointment():
    intendedLoops = configurator.PIM_ADD_APPOINTMENT_COUNTER
    cmd = PrepareUIAutomatorCmd('borqs.test.CalendarTest', 'testAddCalendarAppointment', 'mtbf.jar', intendedLoops)
    executeWaitAndReport(cmd, intendedLoops, INTERVAL_TIME)


def Add_Alarm():
    intendedLoops = configurator.PIM_ADD_ALARM_COUNTER
    cmd = PrepareUIAutomatorCmd('borqs.test.ClockTest', 'testCreateAlarm', 'mtbf.jar', intendedLoops)
    executeWaitAndReport(cmd, intendedLoops, INTERVAL_TIME)


def Delete_Appointment():
    intendedLoops = configurator.PIM_DELETE_APPOINTMENT_COUNTER
    cmd = PrepareUIAutomatorCmd('borqs.test.CalendarTest', 'testDeleteCalendarAppointment', 'mtbf.jar', intendedLoops)
    executeWaitAndReport(cmd, intendedLoops, INTERVAL_TIME)


def Delete_Alarm():
    intendedLoops = configurator.PIM_DELETE_ALARM_COUNTER
    cmd = PrepareUIAutomatorCmd('borqs.test.ClockTest', 'testDeleteAlarm', 'mtbf.jar', intendedLoops)
    executeWaitAndReport(cmd, intendedLoops, INTERVAL_TIME)


# =============  MULTIMEDIA ===============

def MultiMedia():
    global g_logger, g_loop_counter, g_tempCount, g_total_crashcount, g_loop_Crash, g_crash_text
    g_tempCount = 0
    g_crash_text = ''
    # Device_Sleep(2)
    printBeginLogsL1()
    g_logger.collectLogs(MultiMedia.func_name)

    start_time = getDeviceCurrentTime()
    printBetweenLogsL1('Starting tests...')
    printBetweenLogsL1('Start Time = ' + str(start_time))

    Record_Video()
    Playback_Video()
    Delete_Video()
    Take_Picture()
    Open_Picture()
    Delete_Picture()
    Record_Audio()
    Playback_Audio()
    Delete_Audio()
    Play_Video_Streaming()
    Open_Close_MusicPlayer()
    Open_Play_Close_Music()

    # Device_Sleep(2)


    global g_total_crashcount, g_loop_Crash
    # print "loop crash",g_loop_Crash
    # print "totoal crash",g_total_crashcount
    # print "totoal crash",g_tempCount
    g_loop_Crash = int(g_loop_Crash) + int(g_total_crashcount)
    # print "loop crash",g_loop_Crash
    end_time = getDeviceCurrentTime()
    printBetweenLogsL1('Done')
    printBetweenLogsL1('End Time = ' + str(end_time))
    printBetweenLogsL1('Duration - ' + str(end_time - start_time))
    printBetweenLogsL1('Intended total - ' + str(g_testcase_intended_total))
    printBetweenLogsL1('Actual total - ' + str(g_testcase_act_total))
    printBetweenLogsL1('Actual passed - ' + str(g_testcase_pass))
    printBetweenLogsL1('Actual failures - ' + str(g_testcase_fail))

    g_logger.stopLogCollection(MultiMedia.func_name)
    g_logger.Clear_Logs_sdcard()
    remarks = REMARK_OK
    if g_testcase_act_total != g_testcase_intended_total:
        remarks = remarks + REMARK_LESS_THAN_INTENDED

    successRate = 0
    if g_testcase_intended_total > 0:
        successRate = float(g_testcase_pass) / float(g_testcase_intended_total) * 100
    if successRate < g_required_pass_rate:
        remarks = remarks + REMARK_LOW_PASS_RATE

    g_crash_text = g_logger.getCrashText(MultiMedia.func_name, g_tempCount)
    # print "crash text is",g_crash_text
    g_reporter.writeReport(inspect.stack()[0][3], SUMMARY, g_testcase_intended_total, start_time, end_time,
                           g_testcase_act_total, g_testcase_pass, g_testcase_fail, remarks, SUMMARY)

    util.removeScreenShotFolder(g_loop_counter)

    printEndLogsL1()
    if g_kill_processes == True:
        g_logger.CleanUpProcesses()
    if g_kill_All_Apps == True:
        util.KillAllApps()


def Record_Audio():
    intendedLoops = configurator.MULTIMEDIA_RECORD_AUDIO_COUNTER
    cmd = PrepareUIAutomatorCmd('borqs.test.MultimediaTest', 'testRecordAudio', 'mtbf.jar', intendedLoops)
    executeWaitAndReport(cmd, intendedLoops, INTERVAL_TIME)


def Playback_Audio():
    intendedLoops = configurator.MULTIMEDIA_PLAYBACK_AUDIO_COUNTER
    cmd = PrepareUIAutomatorCmd('borqs.test.MultimediaTest', 'testRecord_Playback', 'mtbf.jar', intendedLoops)
    executeWaitAndReport(cmd, intendedLoops, INTERVAL_TIME)


def Delete_Audio():
    intendedLoops = configurator.MULTIMEDIA_DELETE_AUDIO_COUNTER
    cmd = PrepareUIAutomatorCmd(PROJECT_NAME+'MultimediaTest', 'testRecord_Delete')
    executeWaitAndReport(cmd, intendedLoops, INTERVAL_TIME)


def Take_Picture():
    intendedLoops = configurator.MULTIMEDIA_TAKE_PICTURE_COUNTER
    cmd = PrepareUIAutomatorCmd('borqs.test.MultimediaTest', 'testCapturePicture', 'mtbf.jar', intendedLoops)
    executeWaitAndReport(cmd, intendedLoops, INTERVAL_TIME)


def Open_Picture():
    intendedLoops = configurator.MULTIMEDIA_OPEN_PICTURE_COUNTER
    cmd = PrepareUIAutomatorCmd('borqs.test.MultimediaTest', 'testViewPicture', 'mtbf.jar', intendedLoops)
    executeWaitAndReport(cmd, intendedLoops, INTERVAL_TIME)


def Delete_Picture():
    intendedLoops = configurator.MULTIMEDIA_DELETE_PICTURE_COUNTER
    cmd = PrepareUIAutomatorCmd('borqs.test.MultimediaTest', 'testDeletePicture', 'mtbf.jar', intendedLoops)
    executeWaitAndReport(cmd, intendedLoops, INTERVAL_TIME)


def Record_Video():
    intendedLoops = configurator.MULTIMEDIA_RECORD_VIDEO_COUNTER
    cmd = PrepareUIAutomatorCmd('borqs.test.MultimediaTest', 'testCaptureVideo', 'mtbf.jar', intendedLoops)
    executeWaitAndReport(cmd, intendedLoops, INTERVAL_TIME)


def Playback_Video():
    intendedLoops = configurator.MULTIMEDIA_PLAYBACK_VIDEO_COUNTER
    cmd = PrepareUIAutomatorCmd('borqs.test.MultimediaTest', 'testViewVideo', 'mtbf.jar', intendedLoops)
    executeWaitAndReport(cmd, intendedLoops, INTERVAL_TIME)


def Delete_Video():
    intendedLoops = configurator.MULTIMEDIA_DELETE_VIDEO_COUNTER
    cmd = PrepareUIAutomatorCmd('borqs.test.MultimediaTest', 'testDeleteVideo', 'mtbf.jar', intendedLoops)
    executeWaitAndReport(cmd, intendedLoops, INTERVAL_TIME)


def Play_Video_Streaming():
    intendedLoops = configurator.MULTIMEDIA_PLAY_STREAMING_VIDEO_COUNTER
    cmd = PrepareUIAutomatorCmd('borqs.test.StreamingTest', 'testStreaming', 'mtbf.jar', intendedLoops)
    executeWaitAndReport(cmd, intendedLoops, INTERVAL_TIME)


def Open_Close_MusicPlayer():
    intendedLoops = configurator.MULTIMEDIA_OPEN_CLOSE_MUSIC_PLAYER_COUNTER
    cmd = PrepareUIAutomatorCmd('borqs.test.MultimediaTest', 'testOpenCloseMusicPlayer', 'mtbf.jar', intendedLoops)
    executeWaitAndReport(cmd, intendedLoops, INTERVAL_TIME)


def Open_Play_Close_Music():
    intendedLoops = configurator.MULTIMEDIA_OPEN_PLAY_MUSIC_CLOSE_COUNTER
    cmd = PrepareUIAutomatorCmd('borqs.test.MultimediaTest', 'testOpenClosePlayMusicPlayer', 'mtbf.jar', intendedLoops)
    executeWaitAndReport(cmd, intendedLoops, INTERVAL_TIME)


# ============= MULTITASKING ===============
def MultiTask():
    global g_logger, g_tempCount, g_total_crashcount, g_loop_Crash, g_loop_counter, g_crash_text
    g_tempCount = 0
    g_crash_text = ''
    printBeginLogsL1()
    g_logger.collectLogs(MultiTask.func_name)

    start_time = getDeviceCurrentTime()
    printBetweenLogsL1('Starting tests...')
    printBetweenLogsL1('Start Time = ' + str(start_time))

    Switch_App_Chrome()
    Close_Chrome()

    g_loop_Crash = int(g_loop_Crash) + int(g_total_crashcount)
    end_time = getDeviceCurrentTime()
    printBetweenLogsL1('Done')
    printBetweenLogsL1('End Time = ' + str(end_time))
    printBetweenLogsL1('Duration - ' + str(end_time - start_time))
    printBetweenLogsL1('Intended total - ' + str(g_testcase_intended_total))
    printBetweenLogsL1('Actual total - ' + str(g_testcase_act_total))
    printBetweenLogsL1('Actual passed - ' + str(g_testcase_pass))
    printBetweenLogsL1('Actual failures - ' + str(g_testcase_fail))

    g_logger.stopLogCollection(MultiTask.func_name)
    g_logger.Clear_Logs_sdcard()
    remarks = REMARK_OK
    if g_testcase_act_total != g_testcase_intended_total:
        remarks = remarks + REMARK_LESS_THAN_INTENDED

    successRate = 0
    if g_testcase_intended_total > 0:
        successRate = float(g_testcase_pass) / float(g_testcase_intended_total) * 100
    if successRate < g_required_pass_rate:
        remarks = remarks + REMARK_LOW_PASS_RATE

    g_crash_text = g_logger.getCrashText(MultiTask.func_name, g_tempCount)
    # print "crash text is",g_crash_text
    g_reporter.writeReport(inspect.stack()[0][3], SUMMARY, g_testcase_intended_total, start_time, end_time,
                           g_testcase_act_total, g_testcase_pass, g_testcase_fail, remarks, SUMMARY)

    util.removeScreenShotFolder(g_loop_counter)

    printEndLogsL1()
    if g_kill_processes == True:
        g_logger.CleanUpProcesses()
    if g_kill_All_Apps == True:
        util.KillAllApps()


def Switch_Apps_With_Call():
    global g_to_be_retried, g_remaining_loop_count
    g_to_be_retried = False
    intendedLoops = configurator.MULTITASK_WITH_CALL
    cmd = prepareCommand('borqs.stabilitytest.settings.MultiTaskCall', 'testMultitaskingWithCall',
                         'borqs.stabilitytest.settings', '.AT_ST_Settings_TestRunner', intendedLoops)
    executeWaitAndReportActual(cmd, intendedLoops, INTERVAL_TIME)
    if True == g_to_be_retried:
        Dummy_TestCase_For_Call_PhoneA()
        # Dummy_TestCase_For_Call_PhoneB()
        newcmd = prepareCommand('borqs.stabilitytest.settings.MultiTaskCall', 'testMultitaskingWithCall',
                                'borqs.stabilitytest.settings', '.AT_ST_Settings_TestRunner', g_remaining_loop_count)
        executeWaitAndReportActual(newcmd, (g_remaining_loop_count + 1), INTERVAL_TIME)
        g_to_be_retried = False
        g_remaining_loop_count = 0


def Switch_Apps_With_Browser():
    global g_to_be_retried, g_remaining_loop_count, g_logger, g_kill_All_Apps
    g_to_be_retried = False
    intendedLoops = configurator.MULTITASK_WITH_BROWSER
    cmd = prepareCommand('borqs.instrumentationtest.browser.MultiTaskBrowser', 'testMultitaskingWithBrowser',
                         'borqs.instrumentationtest.browser', '.AT_ST_Browser_Runner', intendedLoops)
    executeWaitAndReportActual(cmd, intendedLoops, INTERVAL_TIME)
    if True == g_to_be_retried:
        if g_kill_All_Apps == True:
            util.KillAllApps()
        newcmd = prepareCommand('borqs.instrumentationtest.browser.MultiTaskBrowser', 'testMultitaskingWithBrowser',
                                'borqs.instrumentationtest.browser', '.AT_ST_Browser_Runner', g_remaining_loop_count)
        executeWaitAndReportActual(newcmd, (g_remaining_loop_count + 1), INTERVAL_TIME)
        g_to_be_retried = False
        g_remaining_loop_count = 0


def Switch_App_Chrome():
    intendedLoops = configurator.MULTITASK_SWITCH_APP_CHROME
    cmd = PrepareUIAutomatorCmd('borqs.test.MultimediaTest', 'testMultitask_Chrome_SwitchApps', 'mtbf.jar',
                                intendedLoops)
    executeWaitAndReport(cmd, intendedLoops, INTERVAL_TIME)


def Close_Chrome():
    intendedLoops = configurator.MULTITASK_CLOSE_CHROME
    cmd = PrepareUIAutomatorCmd('borqs.test.MultimediaTest', 'testMultitask_CloseBrowser', 'mtbf.jar', intendedLoops)
    executeWaitAndReport(cmd, intendedLoops, INTERVAL_TIME)


# ============= 5.1.10 MENUNAVIGATION ===============
def Menu_Nav():
    util.pylogger.warn('\n\n ====  Started setting View Server ===\n\n\n')
    ret = commands.getoutput('adb -s ' + g_device_A_id + ' shell service call window 2 i32 4939')
    ret = commands.getoutput('adb -s ' + g_device_A_id + ' shell service call window 1 i32 4939')
    util.pylogger.warn('Returned Result : ' + str(ret) + '\n')
    if str(ret).find('Result: Parcel(00000000 00000001') == -1:
        util.pylogger.warn(
            '\n\n\n === Failed to start View Server in 1st attempt \n\n === Returned result : ' + str(ret) + '\n\n')
        ret = commands.getoutput('adb -s ' + g_device_A_id + ' shell service call window 2 i32 4939')
        ret = commands.getoutput('adb -s ' + g_device_A_id + ' shell service call window 1 i32 4939')
        util.pylogger.warn('Returned Result in second attempt : ' + str(ret) + '\n')
        if str(ret).find('Result: Parcel(00000000 00000001') == -1:
            util.pylogger.warn('\n\n === Failed to start View Server in 2nd attempt  === \n')
        else:
            util.pylogger.warn('\n\n === View Server started in 2nd attempt ===\n\n')
    else:
        util.pylogger.warn('\n\n=== View Server started in 1st attempt ===\n\n')

    global g_logger, g_tempCount, g_total_crashcount, g_loop_Crash
    g_tempCount = 0
    printBeginLogsL1()
    g_logger.collectLogs(Menu_Nav.func_name)
    start_time = getDeviceCurrentTime()
    printBetweenLogsL1('Starting tests...')
    printBetweenLogsL1('Start Time = ' + str(start_time))

    Menu_Nav_Browser()
    Menu_Nav_Calculator()
    Menu_Nav_Calendar()
    Menu_Nav_Clock()
    Menu_Nav_Contact()
    # Menu_Nav_Gmail()
    Menu_Nav_Launcher()
    Menu_Nav_Camera()
    # Commented as Camera UI is different
    Menu_Nav_Photos()  # Commented as Task application not present
    Menu_Nav_SoundRecorder()  # Commented as Sound Recorder application is not present
    Menu_Nav_Music()

    g_loop_Crash = int(g_loop_Crash) + int(g_total_crashcount)
    end_time = getDeviceCurrentTime()
    printBetweenLogsL1('Done')
    printBetweenLogsL1('End Time = ' + str(end_time))
    printBetweenLogsL1('Duration - ' + str(end_time - start_time))
    printBetweenLogsL1('Intended total - ' + str(g_testcase_intended_total))
    printBetweenLogsL1('Actual total - ' + str(g_testcase_act_total))
    printBetweenLogsL1('Actual passed - ' + str(g_testcase_pass))
    printBetweenLogsL1('Actual failures - ' + str(g_testcase_fail))

    g_logger.stopLogCollection(Menu_Nav.func_name)
    g_logger.Clear_Logs_sdcard()
    remarks = REMARK_OK
    if g_testcase_act_total != g_testcase_intended_total:
        remarks = remarks + REMARK_LESS_THAN_INTENDED

    successRate = 0
    if g_testcase_intended_total > 0:
        successRate = float(g_testcase_pass) / float(g_testcase_intended_total) * 100
    if successRate < g_required_pass_rate:
        remarks = remarks + REMARK_LOW_PASS_RATE
    g_crash_text = g_logger.getCrashText(Menu_Nav.func_name, g_tempCount)
    # print "crash text is",g_crash_text
    g_reporter.writeReport(inspect.stack()[0][3], SUMMARY, g_testcase_intended_total, start_time, end_time,
                           g_testcase_act_total, g_testcase_pass, g_testcase_fail, remarks, SUMMARY)

    printEndLogsL1()
    if g_kill_processes == True:
        g_logger.CleanUpProcesses()
    if g_kill_All_Apps == True:
        util.KillAllApps()


def Retry_Menu_Nav(cmd, intendedLoops, INTERVAL_TIME):
    global g_to_be_retried
    if True == g_to_be_retried:
        executeWaitAndReportActual(cmd, intendedLoops, INTERVAL_TIME)
        g_to_be_retried = False


def Menu_Nav_Browser():
    intendedLoops = configurator.MENU_NAV_BROWSER_COUNTER
    cmd = PrepareUIAutomatorCmd('borqs.test.MenuNavTest', 'testBrowserMenuNavigation', 'mtbf.jar', intendedLoops)
    executeWaitAndReport(cmd, intendedLoops, INTERVAL_TIME)


def Menu_Nav_Calculator():
    intendedLoops = configurator.MENU_NAV_CALCULATOR_COUNTER
    cmd = PrepareUIAutomatorCmd('borqs.test.MenuNavTest', 'testCalculatorMenuNavigation', 'mtbf.jar', intendedLoops)
    executeWaitAndReport(cmd, intendedLoops, INTERVAL_TIME)


def Menu_Nav_Calendar():
    intendedLoops = configurator.MENU_NAV_CALENDAR_COUNTER
    cmd = PrepareUIAutomatorCmd('borqs.test.MenuNavTest', 'testCalendarMenuNavigation', 'mtbf.jar', intendedLoops)
    executeWaitAndReport(cmd, intendedLoops, INTERVAL_TIME)


def Menu_Nav_Clock():
    intendedLoops = configurator.MENU_NAV_CLOCK_COUNTER
    cmd = PrepareUIAutomatorCmd('borqs.test.MenuNavTest', 'testClockMenuNavigation', 'mtbf.jar', intendedLoops)
    executeWaitAndReport(cmd, intendedLoops, INTERVAL_TIME)


def Menu_Nav_Contact():
    intendedLoops = configurator.MENU_NAV_CONTACTS_COUNTER
    cmd = PrepareUIAutomatorCmd('borqs.test.MenuNavTest', 'testContactMenuNavigation', 'mtbf.jar', intendedLoops)
    executeWaitAndReport(cmd, intendedLoops, INTERVAL_TIME)


def Menu_Nav_Camera():
    intendedLoops = configurator.MENU_NAV_CAMERA_COUNTER
    cmd = PrepareUIAutomatorCmd('borqs.test.MenuNavTest', 'testCameraMenuNavigation', 'mtbf.jar', intendedLoops)
    executeWaitAndReport(cmd, intendedLoops, INTERVAL_TIME)


def Menu_Nav_Launcher():
    intendedLoops = configurator.MENU_NAV_LAUNCHER_COUNTER
    cmd = PrepareUIAutomatorCmd('borqs.test.MenuNavTest', 'testLauncherMenuNavigation', 'mtbf.jar', intendedLoops)
    executeWaitAndReport(cmd, intendedLoops, INTERVAL_TIME)


def Menu_Nav_Photos():
    intendedLoops = configurator.MENU_NAV_PHOTOS_COUNTER
    cmd = PrepareUIAutomatorCmd('borqs.test.MenuNavTest', 'testPhotoMenuNavigation', 'mtbf.jar', intendedLoops)
    executeWaitAndReport(cmd, intendedLoops, INTERVAL_TIME)


def Menu_Nav_Gmail():
    intendedLoops = configurator.MENU_NAV_GMAIL_COUNTER
    cmd = PrepareUIAutomatorCmd('borqs.test.MenuNavTest', 'testGmailMenuNavigation', 'mtbf.jar', intendedLoops)
    executeWaitAndReport(cmd, intendedLoops, INTERVAL_TIME)


def Menu_Nav_Music():
    intendedLoops = configurator.MENU_NAV_MUSIC_COUNTER
    cmd = PrepareUIAutomatorCmd('borqs.test.MenuNavTest', 'testMusicMenuNavigation', 'mtbf.jar', intendedLoops)
    executeWaitAndReport(cmd, intendedLoops, INTERVAL_TIME)


def Menu_Nav_SoundRecorder():
    intendedLoops = configurator.MENU_NAV_SOUNDRECORDER_COUNTER
    cmd = PrepareUIAutomatorCmd('borqs.test.MenuNavTest', 'testSoundRecorderMenuNavigation', 'mtbf.jar', intendedLoops)
    executeWaitAndReport(cmd, intendedLoops, INTERVAL_TIME)


'''
def Menu_Nav_Messaging():
    global g_to_be_retried
    g_to_be_retried = False
    intendedLoops = configurator.MENU_NAV_MESSAGING_COUNTER
    cmd = prepareCommand('borqs.stabilitytest.settings.MenuNavTest', 'testMessagingMenuNavigation', 'borqs.stabilitytest.settings', '.AT_ST_Settings_TestRunner', intendedLoops) 
    executeWaitAndReportActual(cmd, intendedLoops, INTERVAL_TIME) 
    Retry_Menu_Nav(cmd, intendedLoops, INTERVAL_TIME)   
'''


# ============= 5.1.9 WIFI ===============
def WiFi():
    global g_logger
    printBeginLogsL1()
    g_logger.collectLogs(WiFi.func_name)

    start_time = getDeviceCurrentTime()
    printBetweenLogsL1('Starting tests...')
    printBetweenLogsL1('Start Time = ' + str(start_time))

    WiFi_Radio_On_Off()
    WiFi_Network_Connect_Disconnect()

    end_time = getDeviceCurrentTime()
    printBetweenLogsL1('Done')
    printBetweenLogsL1('End Time = ' + str(end_time))
    printBetweenLogsL1('Duration - ' + str(end_time - start_time))
    printBetweenLogsL1('Intended total - ' + str(g_testcase_intended_total))
    printBetweenLogsL1('Actual total - ' + str(g_testcase_act_total))
    printBetweenLogsL1('Actual passed - ' + str(g_testcase_pass))
    printBetweenLogsL1('Actual failures - ' + str(g_testcase_fail))

    g_logger.stopLogCollection(WiFi.func_name)
    g_logger.Clear_Logs_sdcard()
    remarks = REMARK_OK
    if g_testcase_act_total != g_testcase_intended_total:
        remarks = remarks + REMARK_LESS_THAN_INTENDED

    successRate = 0
    if g_testcase_intended_total > 0:
        successRate = float(g_testcase_pass) / float(g_testcase_intended_total) * 100
    if successRate < g_required_pass_rate:
        remarks = remarks + REMARK_LOW_PASS_RATE
    # g_reporter.writeReport(inspect.stack()[0][3], SUMMARY, g_testcase_intended_total, start_time, end_time,  g_testcase_act_total, g_testcase_pass, g_testcase_fail, g_tempCount, remarks, SUMMARY)
    g_reporter.writeReport(inspect.stack()[0][3], SUMMARY, g_testcase_intended_total, start_time, end_time,
                           g_testcase_act_total, g_testcase_pass, g_testcase_fail, remarks, SUMMARY)

    printEndLogsL1()
    if g_kill_processes == True:
        g_logger.CleanUpProcesses()
    if g_kill_All_Apps == True:
        util.KillAllApps()


def WiFi_Radio_On_Off():
    intendedLoops = configurator.WIFI_RADIO_ON_OFF_COUNTER
    cmd = PrepareUIAutomatorCmd('borqs.test.WifiTest', 'testToggleWifi', 'mtbf.jar', intendedLoops)
    executeWaitAndReport(cmd, intendedLoops, INTERVAL_TIME)


def WiFi_Network_Connect_Disconnect():
    intendedLoops = configurator.WIFI_NETWORK_CONNECT_DISCONNECT_COUNTER
    cmd = PrepareUIAutomatorCmd('borqs.test.WifiTest', 'testConnectDisconnectNetwork', 'mtbf.jar', intendedLoops)
    executeWaitAndReport(cmd, intendedLoops, INTERVAL_TIME)


# ============= 5.1.12 Volte ===============
def VolteTelephony():
    global g_logger
    printBeginLogsL1()
    g_logger.collectLogs(VolteTelephony.func_name)

    start_time = getDeviceCurrentTime()
    printBetweenLogsL1('Starting tests...')
    printBetweenLogsL1('Start Time = ' + str(start_time))

    MO_Volte_Phonebook()
    time.sleep(1)
    MO_Volte_Call_History()
    time.sleep(1)
    MT_Volte()
    time.sleep(1)

    end_time = getDeviceCurrentTime()
    printBetweenLogsL1('Done')
    printBetweenLogsL1('End Time = ' + str(end_time))
    printBetweenLogsL1('Duration - ' + str(end_time - start_time))
    printBetweenLogsL1('Intended total - ' + str(g_testcase_intended_total))
    printBetweenLogsL1('Actual total - ' + str(g_testcase_act_total))
    printBetweenLogsL1('Actual passed - ' + str(g_testcase_pass))
    printBetweenLogsL1('Actual failures - ' + str(g_testcase_fail))

    g_logger.stopLogCollection(VolteTelephony.func_name)
    g_logger.Clear_Logs_sdcard()
    remarks = REMARK_OK
    if g_testcase_act_total != g_testcase_intended_total:
        remarks = remarks + REMARK_LESS_THAN_INTENDED

    successRate = 0
    if g_testcase_intended_total > 0:
        successRate = float(g_testcase_pass) / float(g_testcase_intended_total) * 100
    if successRate < g_required_pass_rate:
        remarks = remarks + REMARK_LOW_PASS_RATE
    # g_reporter.writeReport(inspect.stack()[0][3], SUMMARY, g_testcase_intended_total, start_time, end_time,  g_testcase_act_total, g_testcase_pass, g_testcase_fail, g_tempCount, remarks, SUMMARY)
    g_reporter.writeReport(inspect.stack()[0][3], SUMMARY, g_testcase_intended_total, start_time, end_time,
                           g_testcase_act_total, g_testcase_pass, g_testcase_fail, remarks, SUMMARY)

    printEndLogsL1()
    if g_kill_processes == True:
        g_logger.CleanUpProcesses()
    if g_kill_All_Apps == True:
        util.KillAllApps()


def MO_Volte_Phonebook1():
    intendedLoops = configurator.MO_VOLTE_PHONEBOOK
    cmd = PrepareUIAutomatorCmd('borqs.test.NumSyncTest', 'testNumsycMOWContact', 'mtbf.jar', intendedLoops)
    # executeWaitAndReport(cmd, intendedLoops, INTERVAL_TIME)
    thread.start_new_thread(executeThreadOnPhone, (cmd, intendedLoops, PHONE_INTERVAL_TIME, g_device_A_id))
    cmd = PrepareUIAutomatorCmdB('borqs.test.NumSyncTest', 'testMTCall', 'mtbf.jar', intendedLoops)
    executeWaitAndReport(cmd, intendedLoops, PHONE_INTERVAL_TIME)
    # thread.exit()
    time.sleep(60)


def MO_Volte_Phonebook():
    intendedLoops = configurator.MO_VOLTE_PHONEBOOK
    cmd = PrepareUIAutomatorCmdB('borqs.test.NumSyncTest', 'testMTCallB', 'mtbf.jar', intendedLoops)
    thread.start_new_thread(executeThreadOnPhone, (cmd, intendedLoops, PHONE_INTERVAL_TIME, g_device_B_id))
    cmd = PrepareUIAutomatorCmd('borqs.test.NumSyncTest', 'testNumsycMOWContact', 'mtbf.jar', intendedLoops)
    executeWaitAndReport(cmd, intendedLoops, INTERVAL_TIME)
    # thread.exit()
    # time.sleep(60)


def MO_Volte_Call_History():
    intendedLoops = configurator.MO_VOLTE_HISTORY
    cmd = PrepareUIAutomatorCmdB('borqs.test.NumSyncTest', 'testMTCallB', 'mtbf.jar', intendedLoops)
    thread.start_new_thread(executeThreadOnPhone, (cmd, intendedLoops, PHONE_INTERVAL_TIME, g_device_B_id))
    cmd = PrepareUIAutomatorCmd('borqs.test.NumSyncTest', 'testNumsycMOCalllog', 'mtbf.jar', intendedLoops)
    executeWaitAndReport(cmd, intendedLoops, INTERVAL_TIME)
    # thread.exit()
    # time.sleep(60)


def MT_Volte():
    global g_to_be_retried, g_remaining_loop_count, PHONE_INTERVAL_TIME
    global g_device_B_id
    g_to_be_retried = False
    intendedLoops = configurator.MT_VOLTE
    # Kick start the Phone B first...in a thread
    cmdPhoneB = PrepareUIAutomatorCmdB('borqs.test.NumSyncTest', 'testNumsycMOCalllogB', 'mtbf.jar', intendedLoops)
    print "cmdPhoneB : ", cmdPhoneB
    thread.start_new_thread(executeThreadOnPhone, (cmdPhoneB, intendedLoops, PHONE_INTERVAL_TIME, g_device_B_id))
    cmd = PrepareUIAutomatorCmd('borqs.test.NumSyncTest', 'testMTCall', 'mtbf.jar', intendedLoops)
    executeWaitAndReport(cmd, intendedLoops, PHONE_INTERVAL_TIME)
    # thread.exit()
    # time.sleep(60)




    # Dummy_TestCase_For_Call_PhoneB()
    # Dummy_TestCase_For_Call_PhoneA()


# ============= 5.1.14 Video ===============
def VideoTelephony():
    global g_logger
    printBeginLogsL1()
    g_logger.collectLogs(VideoTelephony.func_name)

    start_time = getDeviceCurrentTime()
    printBetweenLogsL1('Starting tests...')
    printBetweenLogsL1('Start Time = ' + str(start_time))

    MO_Video_Phonebook()
    MO_Video_History()
    MT_Video()
    SwitchWifiOn()
    MO_Video_WIFI()
    MT_Video_WIFI()
    SwitchWifiOff()

    end_time = getDeviceCurrentTime()
    printBetweenLogsL1('Done')
    printBetweenLogsL1('End Time = ' + str(end_time))
    printBetweenLogsL1('Duration - ' + str(end_time - start_time))
    printBetweenLogsL1('Intended total - ' + str(g_testcase_intended_total))
    printBetweenLogsL1('Actual total - ' + str(g_testcase_act_total))
    printBetweenLogsL1('Actual passed - ' + str(g_testcase_pass))
    printBetweenLogsL1('Actual failures - ' + str(g_testcase_fail))

    g_logger.stopLogCollection(VideoTelephony.func_name)
    g_logger.Clear_Logs_sdcard()
    remarks = REMARK_OK
    if g_testcase_act_total != g_testcase_intended_total:
        remarks = remarks + REMARK_LESS_THAN_INTENDED

    successRate = 0
    if g_testcase_intended_total > 0:
        successRate = float(g_testcase_pass) / float(g_testcase_intended_total) * 100
    if successRate < g_required_pass_rate:
        remarks = remarks + REMARK_LOW_PASS_RATE
    # g_reporter.writeReport(inspect.stack()[0][3], SUMMARY, g_testcase_intended_total, start_time, end_time,  g_testcase_act_total, g_testcase_pass, g_testcase_fail, g_tempCount, remarks, SUMMARY)
    g_reporter.writeReport(inspect.stack()[0][3], SUMMARY, g_testcase_intended_total, start_time, end_time,
                           g_testcase_act_total, g_testcase_pass, g_testcase_fail, remarks, SUMMARY)

    printEndLogsL1()
    if g_kill_processes == True:
        g_logger.CleanUpProcesses()
    if g_kill_All_Apps == True:
        util.KillAllApps()


def MO_Video_Phonebook():
    intendedLoops = configurator.MO_VOLTE_PHONEBOOK

    cmd = PrepareUIAutomatorCmdB('borqs.test.NumSyncTest', 'testMTVideoCallB', 'mtbf.jar', intendedLoops)
    thread.start_new_thread(executeThreadOnPhone, (cmd, intendedLoops, PHONE_INTERVAL_TIME, g_device_B_id))
    cmd = PrepareUIAutomatorCmd('borqs.test.NumSyncTest', 'testVideoNumsycMOContact', 'mtbf.jar', intendedLoops)
    executeWaitAndReport(cmd, intendedLoops, INTERVAL_TIME)
    # thread.exit()
    time.sleep(60)


def MO_Video_History():
    intendedLoops = configurator.MO_VIDEO_HISTORY

    cmd = PrepareUIAutomatorCmdB('borqs.test.NumSyncTest', 'testMTVideoCallB', 'mtbf.jar', intendedLoops)
    thread.start_new_thread(executeThreadOnPhone, (cmd, intendedLoops, PHONE_INTERVAL_TIME, g_device_B_id))
    cmd = PrepareUIAutomatorCmd('borqs.test.NumSyncTest', 'testVideoNumsycMOCalllog', 'mtbf.jar', intendedLoops)
    executeWaitAndReport(cmd, intendedLoops, INTERVAL_TIME)
    # thread.exit()
    time.sleep(60)


def MT_Video():
    global g_to_be_retried, g_remaining_loop_count, PHONE_INTERVAL_TIME
    global g_device_B_id
    g_to_be_retried = False
    intendedLoops = configurator.MT_VIDEO
    # Kick start the Phone B first...in a thread
    cmdPhoneB = PrepareUIAutomatorCmdB('borqs.test.NumSyncTest', 'testVideoNumsycMOWifiCalllogB', 'mtbf.jar',
                                       intendedLoops)
    print "cmdPhoneB : ", cmdPhoneB
    thread.start_new_thread(executeThreadOnPhone, (cmdPhoneB, intendedLoops, PHONE_INTERVAL_TIME, g_device_B_id))
    cmd = PrepareUIAutomatorCmd('borqs.test.NumSyncTest', 'testMTVideoCall', 'mtbf.jar', intendedLoops)
    executeWaitAndReport(cmd, intendedLoops, PHONE_INTERVAL_TIME)
    # thread.exit()
    time.sleep(60)


def SwitchWifiOn():
    intendedLoops = 1
    cmd = PrepareUIAutomatorCmd('borqs.test.NumSyncTest', 'testAirplaneMode_WifiConnect', 'mtbf.jar', intendedLoops)
    executeWaitAndReport(cmd, intendedLoops, INTERVAL_TIME)


def SwitchWifiOff():
    intendedLoops = 1
    cmd = PrepareUIAutomatorCmd('borqs.test.NumSyncTest', 'testAirplaneMode_WifiDisconnect', 'mtbf.jar', intendedLoops)
    executeWaitAndReport(cmd, intendedLoops, INTERVAL_TIME)


def MO_Video_WIFI():
    intendedLoops = configurator.MO_VIDEO_DAILER_WIFI

    cmd = PrepareUIAutomatorCmdB('borqs.test.NumSyncTest', 'testMTVideoCallB', 'mtbf.jar', intendedLoops)
    thread.start_new_thread(executeThreadOnPhone, (cmd, intendedLoops, PHONE_INTERVAL_TIME, g_device_B_id))
    cmd = PrepareUIAutomatorCmd('borqs.test.NumSyncTest', 'testVideoNumsycMOWifiDailer', 'mtbf.jar', intendedLoops)
    executeWaitAndReport(cmd, intendedLoops, INTERVAL_TIME)
    # thread.exit()
    time.sleep(60)


def MT_Video_WIFI():
    global g_to_be_retried, g_remaining_loop_count, PHONE_INTERVAL_TIME
    global g_device_B_id
    g_to_be_retried = False
    intendedLoops = configurator.MT_VIDEO_WIFI
    # Kick start the Phone B first...in a thread
    cmdPhoneB = PrepareUIAutomatorCmdB('borqs.test.NumSyncTest', 'testVideoNumsycMOWifiCalllogB', 'mtbf.jar',
                                       intendedLoops)
    print "cmdPhoneB : ", cmdPhoneB
    thread.start_new_thread(executeThreadOnPhone, (cmdPhoneB, intendedLoops, PHONE_INTERVAL_TIME, g_device_B_id))
    cmd = PrepareUIAutomatorCmd('borqs.test.NumSyncTest', 'testMTVideoCall', 'mtbf.jar', intendedLoops)
    executeWaitAndReport(cmd, intendedLoops, PHONE_INTERVAL_TIME)
    # thread.exit()


# ============= 5.1.16 Wi-Fi calling ===============
def WifiCalling():
    global g_logger
    printBeginLogsL1()
    g_logger.collectLogs(WifiCalling.func_name)

    start_time = getDeviceCurrentTime()
    printBetweenLogsL1('Starting tests...')
    printBetweenLogsL1('Start Time = ' + str(start_time))

    SwitchWifiOn()
    time.sleep(5)
    MO_WIFI_Phonebook()
    MO_WIFI_Dailer()
    time.sleep(3)
    MT_WIFI()
    SwitchWifiOff()
    time.sleep(60)

    end_time = getDeviceCurrentTime()
    printBetweenLogsL1('Done')
    printBetweenLogsL1('End Time = ' + str(end_time))
    printBetweenLogsL1('Duration - ' + str(end_time - start_time))
    printBetweenLogsL1('Intended total - ' + str(g_testcase_intended_total))
    printBetweenLogsL1('Actual total - ' + str(g_testcase_act_total))
    printBetweenLogsL1('Actual passed - ' + str(g_testcase_pass))
    printBetweenLogsL1('Actual failures - ' + str(g_testcase_fail))

    g_logger.stopLogCollection(WifiCalling.func_name)
    g_logger.Clear_Logs_sdcard()
    remarks = REMARK_OK
    if g_testcase_act_total != g_testcase_intended_total:
        remarks = remarks + REMARK_LESS_THAN_INTENDED

    successRate = 0
    if g_testcase_intended_total > 0:
        successRate = float(g_testcase_pass) / float(g_testcase_intended_total) * 100
    if successRate < g_required_pass_rate:
        remarks = remarks + REMARK_LOW_PASS_RATE
    # g_reporter.writeReport(inspect.stack()[0][3], SUMMARY, g_testcase_intended_total, start_time, end_time,  g_testcase_act_total, g_testcase_pass, g_testcase_fail, g_tempCount, remarks, SUMMARY)
    g_reporter.writeReport(inspect.stack()[0][3], SUMMARY, g_testcase_intended_total, start_time, end_time,
                           g_testcase_act_total, g_testcase_pass, g_testcase_fail, remarks, SUMMARY)

    printEndLogsL1()
    if g_kill_processes == True:
        g_logger.CleanUpProcesses()
    if g_kill_All_Apps == True:
        util.KillAllApps()


def SwitchWifiOn():
    intendedLoops = 1
    cmd = PrepareUIAutomatorCmd('borqs.test.NumSyncTest', 'testAirplaneMode_WifiConnect', 'mtbf.jar', intendedLoops)
    executeWaitAndReport(cmd, intendedLoops, INTERVAL_TIME)


def SwitchWifiOff():
    intendedLoops = 1
    cmd = PrepareUIAutomatorCmd('borqs.test.NumSyncTest', 'testAirplaneMode_WifiDisconnect', 'mtbf.jar', intendedLoops)
    executeWaitAndReport(cmd, intendedLoops, INTERVAL_TIME)


def MO_WIFI_Phonebook():
    intendedLoops = configurator.MO_WIFI_PHONEBOOK

    cmd = PrepareUIAutomatorCmdB('borqs.test.NumSyncTest', 'testMTCallB', 'mtbf.jar', intendedLoops)
    thread.start_new_thread(executeThreadOnPhone, (cmd, intendedLoops, PHONE_INTERVAL_TIME, g_device_B_id))
    cmd = PrepareUIAutomatorCmd('borqs.test.NumSyncTest', 'testNumsycMOWifiContact', 'mtbf.jar', intendedLoops)
    executeWaitAndReport(cmd, intendedLoops, INTERVAL_TIME)
    # thread.exit()
    # time.sleep(60)


def MO_WIFI_Dailer():
    intendedLoops = configurator.MO_WIFI_HISTORY

    cmd = PrepareUIAutomatorCmdB('borqs.test.NumSyncTest', 'testMTCallB', 'mtbf.jar', intendedLoops)
    thread.start_new_thread(executeThreadOnPhone, (cmd, intendedLoops, PHONE_INTERVAL_TIME, g_device_B_id))
    cmd = PrepareUIAutomatorCmd('borqs.test.NumSyncTest', 'testNumsycMOWifiDailer', 'mtbf.jar', intendedLoops)
    executeWaitAndReport(cmd, intendedLoops, INTERVAL_TIME)
    # thread.exit()
    # time.sleep(60)


def MT_WIFI():
    global g_to_be_retried, g_remaining_loop_count, PHONE_INTERVAL_TIME
    global g_device_B_id
    g_to_be_retried = False
    intendedLoops = configurator.MT_WIFI
    # Kick start the Phone B first...in a thread
    cmdPhoneB = PrepareUIAutomatorCmdB('borqs.test.NumSyncTest', 'testNumsycMOWifiCallLogB', 'mtbf.jar', intendedLoops)
    print "cmdPhoneB : ", cmdPhoneB
    thread.start_new_thread(executeThreadOnPhone, (cmdPhoneB, intendedLoops, PHONE_INTERVAL_TIME, g_device_B_id))
    cmd = PrepareUIAutomatorCmd('borqs.test.NumSyncTest', 'testMTCall', 'mtbf.jar', intendedLoops)
    executeWaitAndReport(cmd, intendedLoops, PHONE_INTERVAL_TIME)
    # thread.exit()
    # time.sleep(60)


