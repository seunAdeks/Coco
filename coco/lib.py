import random, string
import bisect
from datetime import datetime
from collections import OrderedDict
from flask.globals import request
from db_helper import *
from xhtml2pdf import pisa
from cStringIO import StringIO
import tkFileDialog
import Tkinter as tk

# import celery
class Library:

    MARK_COLOR = 'grey'
    db_assist = DBAssistant()

    @staticmethod
    def struct_pref(list_pref, COLORPREFS):
        """
        This function structures the lecturers preferences as a dictionary of a dictionary of a list
        of a tuple.
        :param list_pref:
        :param COLORPREFS:
        :var p a dictionary of a dictionary
        :var ppp a dictionary contained in p
        :return:

        """
        p = {}
        for l in list_pref:
            p[l[0]] = []

        for x in list_pref:
            curr = ""
            for column in x:
                if isinstance(column, int):
                    column = COLORPREFS[column]
                if column in p:
                    curr = column
                if column not in p:
                    p[curr].append(column)

        for key in p:
            p[key] = [tuple(p[key][i:i + 4]) for i in range(0, len(p[key]), 4)]
        ppp = p
        for key in ppp:
            pp = {}
            for l in ppp[key]:
                if l[0] not in pp:
                    pp[l[0]] = [l[1:]]
                else:
                    pp[l[0]].append(tuple(l[1:]))
            p[key] = pp
        return p

    @staticmethod
    def time_mapping(val):
        times_map = {'08.00 - 10.00': 1, '10.00 - 12.00': 2, '12.00 - 14.00': 3, '14.00 - 16.00': 4, '16.00 - 18.00': 5}
        if isinstance(val, str):
            return times_map[val]
        else:
            for key, value in times_map.iteritems():
                if value == val:
                    return key

    @staticmethod
    def color_mapping(val):
        color_map = {'tomato': 0, 'yellow': 2, 'lightgreen': 3}
        return color_map[val]

    @staticmethod
    def assign_lecturehalls(halls, capacity):
        res = []
        for key in halls:
            if capacity >= 200:
                if halls[key] >= capacity:
                    res.append(key)
                    continue
            elif capacity >= 100:
                if 200 > halls[key] >= capacity:
                    res.append(key)
                    continue
            elif capacity < 100:
                if capacity <= halls[key] <= 100:
                    res.append(key)
                    continue
        return res

    @staticmethod
    def struct_courses(id, info):
        lst = [i.lstrip(" ") for i in str(info).split(",")]
        lst.append(id)
        return [int(i) if str(i).isdigit() else i for i in lst]

    @staticmethod
    def struct_rooms(rooms_lst):
        rooms_capacity = {}
        for r in rooms_lst:
            rooms_capacity[str(r[0]) + ", " + str(r[1])] = r[2]
        return rooms_capacity

    @staticmethod
    def struct_constraint(preferences, rooms):
        lectureHalls = Library.struct_rooms(rooms)
        constraint_structure = {}
        for course in preferences:
            temp_list = []
            for days in preferences[course]:
                for tupp in preferences[course][days]:
                    halls = Library.assign_lecturehalls(lectureHalls, int(tupp[2]))
                    for h in halls:
                        temp_list.append(
                                (str(days), Library.time_mapping(str(tupp[0])), h,
                                 Library.color_mapping(tupp[1])))
            constraint_structure[str(course) + "0"] = temp_list
            constraint_structure[str(course) + "1"] = temp_list
        return constraint_structure

    @staticmethod
    def time_difference(t1, t2):
        """
        Finds the difference between two dates in hours.
        :param t1:
        :param t2:
        :return: hrs - Number of hours as a string
        """

        fmt = '%H.%M'
        hrs = str(datetime.strptime(t2.split("-")[0].strip(), fmt) - datetime.strptime(t1.split("-")[0].strip(),
                                                                                       fmt)).split(":")[0]
        return hrs

    @staticmethod
    def read_timeslot_marks(request, param, schedule):
        """
        This function reads timeslot marks, set by user.

        :param: request:form - source form
        :param: param:string - value, which indicates unmarked timeslot
        :param: schedule:boolean - shows if marks are read from the schedule
        :return: preferences:array - marked timeslots
        """
        preferences = []
        for i in range(0, 5):  # timeslot
            for j in range(0, 5):  # week_day
                x = str(i) + str(j)
                if schedule:
                    info = request.form[x].split(':', 2)
                    if info[0] != '0':
                        course_id = Library.get_courseid_by_name(info[0])
                        rooms = Library.get_room_to_id()
                        room_id = rooms[info[1]]
                        preferences.append((j + 1, i + 1, course_id, room_id))
                else:
                    preferences.append((j + 1, i + 1, request.form[x]))
        preferences = [a for a in preferences if a[2] != param]
        return preferences

    @staticmethod
    def form_marks(marks, colors, set_reason, coord, room):
        # TODO: call with parameters for: adding reason text
        """
        This function creates dictionaries with data, structured in a way, better for visual representation on a calendar.

        :param marks:set of rows - original data
        :param colors:list - set of colors for marking the timeslots
        :param set_reason: boolean - indicates whether reason text should be included into output dictionary
        :param coord: boolean - indicates whether the output dictionary is used by study coordinator preference view ( has one more nested level of dictionary)
        :return p: dictionary - restructured input data for better visual representation
        """

        p = {}
        for l in marks:  # dictionary for every day of week
            p[l[0] - 1] = []

        if coord:
            for x in marks:
                p[x[0] - 1].append(x[1])
                p[x[0] - 1].append(x[2] - 1)
                p[x[0] - 1].append(x[3])
                if colors:
                    p[x[0] - 1].append(colors[x[3]])
                else:
                    p[x[0] - 1].append(Library.MARK_COLOR)

        else:
            for x in marks:
                p[x[0] - 1].append(x[1] - 1)
                p[x[0] - 1].append(x[2])
                if colors:
                    p[x[0] - 1].append(colors[x[2]])
                else:
                    p[x[0] - 1].append(Library.MARK_COLOR)
                if set_reason and not room:
                    p[x[0] - 1].append(x[3])
                if room:
                    p[x[0] - 1].append(x[3])
                    p[x[0] - 1].append(x[4] + ", " + x[5])
        if room:
            tuple_length = 5
        else:
            if set_reason:
                tuple_length = 4
            else:
                tuple_length = 3
        for key in p:
            p[key] = [tuple(p[key][i:i + tuple_length]) for i in
                      range(0, len(p[key]), tuple_length)]  # get tuples (timeslot, value, color, [reason text])

        ppp = p

        for key in ppp:
            pp = {}
            if coord:
                for l in ppp[key]:
                    pp[l[0]] = {}
            for l in ppp[key]:
                if coord:
                    #                 if l[1] not in pp[l[0]]:
                    pp[l[0]][l[1]] = [l[2:]]
                # else:
                #                     pp[l[0]][l[1]].append(tuple(l[2:]))
                else:
                    if l[0] not in pp:
                        pp[l[0]] = [l[1:]]
                    else:
                        pp[l[0]].append(tuple(l[1:]))
                p[key] = pp
        return p

    @staticmethod
    def handle_duplicates(marks, savedMarks):
        """
        This function handles marked timeslots. It compares current marks
        with marks saved in database. If the preference for timeslot is new,
        changed or deleted - includes into the array accordingly.

        :param: marks:array - current marks input
        :param: savedMarks:dictionary - marks for current user saved in database
        :return: marks:array - new marks
        :return: upd:array - marks to be updated in DB
        :return: rmv:array - marks to be deleteed from DB
        """
        # weekday_id, timeslot_id, value
        dupl = []
        rmv = []
        upd = []
        new_marks = []
        for p in marks:  # for all marks
            if p[0] - 1 in savedMarks:  # weekday
                if p[1] - 1 in savedMarks[p[0] - 1]:  # timeslot
                    if savedMarks[p[0] - 1][p[1] - 1][0][0] == int(p[2]):  # value
                        dupl.append(p)
                    else:
                        dupl.append(p)
                        upd.append(p)

        mas = Library.dict_to_array(savedMarks)
        tmp = mas
        for x in tmp:
            for u in upd:
                if x[0] == u[0] and x[1] == u[1]:
                    mas.remove(x)
        rmv = set(mas) - set(marks)
        marks = [a for a in marks if a not in dupl]
        return (marks, upd, list(rmv))

    @staticmethod
    def dict_to_array(dict_):
        """
        This function transforms dictionary into an array

        :param: dict_:dicitonary - source dictionary
        :return: arr_:array - transformed input data
        """
        arr_ = []
        for k in dict_.keys():  # weekdays
            for kk in dict_[k].keys():  # timeslots
                arr_.append((k + 1, kk + 1, unicode(dict_[k][kk][0][0])))
        return arr_

    @staticmethod
    def rearrange(dict):
        """
        This function sorts a dictionary based on the value value at the second position in it.
        :param dict:
        :return: sorted

        """
        times_map = {'08.00 - 10.00': 1, '10.00 - 12.00': 2, '12.00 - 14.00': 3, '14.00 - 16.00': 4, '16.00 - 18.00': 5}
        val = 0
        val = times_map[dict[1]]
        return val

    @staticmethod
    def rearrange2(dict):
        """
        This function sorts a dictionary based on the value value at the second position in it.
        :param dict:
        :return: sorted

        """
        tag = {'Monday': 1, 'Tuesday': 2, 'Wednesday': 3, 'Thursday': 4, 'Friday': 5}
        val = 0
        if dict[1] == ():
            val = tag[dict[0]]
        else:
            val = tag[str(dict[1][0])]
        return val

    @staticmethod
    def sorts(dict):
        sorted_list = sorted(dict.items(), key=lambda x: Library.rearrange2(x))

        return OrderedDict(sorted_list)

    @staticmethod
    def validat(week, dict):
        bool = False
        for val in dict.items():
            if val[0] == week:
                bool = True
                break
            if not len(val[1]) == 0 and week == val[1][0]:
                bool = True
                break
        return bool

    @staticmethod
    def groupByTime(dict):
        tag = {1: 'Monday', 2: 'Tuesday', 3: 'Wednesday', 4: 'Thursday', 5: 'Friday'}
        times1, times2, times3, times4, times5 = {}, {}, {}, {}, {}
        for val in dict:
            for course in val.items():
                if course[1][1] == '08.00 - 10.00':
                    times1.update({course[0]: course[1]})
                elif course[1][1] == '10.00 - 12.00':
                    times2.update({course[0]: course[1]})
                elif course[1][1] == '12.00 - 14.00':
                    times3.update({course[0]: course[1]})
                elif course[1][1] == '14.00 - 16.00':
                    times4.update({course[0]: course[1]})
                else:
                    times5.update({course[0]: course[1]})

        for x in range(5):
            if not Library.validat(tag[x + 1], times1):
                times1.update({tag[x + 1]: ()})
            if not Library.validat(tag[x + 1], times2):
                times2.update({tag[x + 1]: ()})
            if not Library.validat(tag[x + 1], times3):
                times3.update({tag[x + 1]: ()})
            if not Library.validat(tag[x + 1], times4):
                times4.update({tag[x + 1]: ()})
            if not Library.validat(tag[x + 1], times5):
                times5.update({tag[x + 1]: ()})

        times1 = Library.sorts(times1)
        times2 = Library.sorts(times2)
        times3 = Library.sorts(times3)
        times4 = Library.sorts(times4)
        times5 = Library.sorts(times5)

        final = (('08.00 - 10.00', times1), ('10.00 - 12.00', times2), ('12.00 - 14.00', times3), ('14.00 - 16.00', times4),
                 ('16.00 - 18.00', times5))
        return OrderedDict(final)

    @staticmethod
    def transform(source_sol, semester_id):
        # weekday_id, timeslot_id, course_id, room_id, semester_id
        end_sol = []
        courses = []
        days = Library.get_weekday_to_id()
        rooms = Library.get_room_to_id()
        for course, val in source_sol.iteritems():
            course_ = Library.db_assist.get_single("select id from courses where course = '" + course[:-1] + "'")
            course_id = course_[0]
            weekday_id = days[val[0]]
            room_id = rooms[val[2]]
            timeslot_id = val[1]
            end_sol.append((weekday_id, timeslot_id, course_id, room_id, semester_id))
        return end_sol

    @staticmethod
    def get_weekday_to_id():
        res = Library.db_assist.get_all("select name, weekday_id from weekdays")
        days = {}
        for x in res:
            days[x[0]] = x[1]
        return days

    @staticmethod
    def get_room_to_id():
        res = Library.db_assist.get_all("select name, location, room_id from rooms")
        rooms = {}
        for x in res:
            rooms[x[0] + ', ' + x[1]] = x[2]
        return rooms
    @staticmethod
    def get_courseid_by_name(course):
        m = Library.db_assist.get_single("select id from courses where course = '" + course+"'")
        res = m if not m else m[0]
        return res

    # @celery.task()
    @staticmethod
    def create_pdf(pdf_data):
        root = tk.Tk()
        root.overrideredirect(True)
        root.geometry('0x0+0+0')
        filename = tkFileDialog.asksaveasfilename(filetypes=[(("PDF", '*.pdf'))],
                                                  defaultextension='.pdf', initialfile='schedule')
        root.withdraw()
        if filename:
            result = open(filename, 'wb')
            pdf = pisa.pisaDocument(StringIO(pdf_data.encode('utf-8')), result)
            #     config = pdfkit.configuration(wkhtmltopdf="C:\Program Files\wkhtmltopdf\\bin")# pdfkit.from_string(html_string, output_file, configuration=config)
            #     css = './static/style.css'
            #     pdf = pdfkit.from_string(StringIO(pdf_data.encode('utf-8')), False, css=css,configuration = config) #return
            #     a = make_response(pdf)
            result.close()
            return True
        return False


    # @celery.task()
    @staticmethod
    def create_attachment(pdf_data):
        pdf = StringIO()
        pisa.CreatePDF(StringIO(pdf_data.encode('utf-8')), pdf)
        return pdf

    @staticmethod
    def rows_to_array(receivers):
        result = []
        for x in receivers:
            result.append(x[0])
        return result

    @staticmethod
    def generate_one_time_password():
        length = 11
        chars = string.ascii_letters + string.digits + '!@#$%^&*()'
        random.seed = (os.urandom(1024))
        return''.join(random.choice(chars) for i in range(length))
