import sys
from scipy.interpolate import CubicSpline
import numpy as np
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm

def resource_path(relative_path):
    """Возвращает корректный путь для доступа к ресурсам после сборки"""
    if hasattr(sys, '_MEIPASS'):
        # Если запущено в распакованном временном каталоге
        base_path = sys._MEIPASS
    else:
        # Если запущено в режиме разработки
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)
pdfmetrics.registerFont(TTFont('DejaVuSans', resource_path('DejaVuSans.ttf')))
pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', resource_path('DejaVuSans-Bold.ttf')))



def get_background_color(r, g, b):
    background_r = 0.9 + 0.1 * r
    background_g = 0.9 + 0.1 * g
    background_b = 0.9 + 0.1 * b
    return [background_r, background_g, background_b]


def stp(x):
    superscript_digits = {
        '0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴',
        '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹',
        '-': '⁻', '+': '⁺', '.': '⋅', '(': '⁽', ')': '⁾'
    }
    s = ""
    for i in str(x):
        s += superscript_digits[i]
    return s


class LogicaPdf:
    def __init__(self, d, pdf, conf, data):
        self.D = d
        self.conf = conf
        self.X, self.Y, self.dX, self.dY, self.degx, self.degy = data
        self.what_it()

        self.c = canvas.Canvas(pdf, pagesize=A4)
        self.c.setFont(self.conf['font'], 2.4 * mm)
        self.c.setStrokeColorRGB(0.6, 0.6, 0.6)
        self.create_ramka(self.conf['color'])
        self.c.setStrokeColorRGB(0, 0, 0)
        if self.D["orientation"]:
            self.rx, self.ry, self.rdx, self.rdy = self.create_vertical_grafik()
        else:
            self.rx, self.ry, self.rdx, self.rdy = self.create_horizontal_grafik()

        if self.D["type"] == "Градуировочный":
            self.graduir()
        elif self.D["type"] == "Наименьшие квадраты":
            self.naim_qv()
        elif self.D["type"] == "Кубический сплайн":
            self.splain()
        self.draw_errors()
        self.c.showPage()
        self.c.save()


    def create_ramka(self, col, lowerx_limit = 5, upperx_limit = 205, lowery_limit = 5, uppery_limit = 295):

        bc = get_background_color(col[0] / 255, col[1] / 255, col[2] / 255)
        self.c.setFillColorRGB(bc[0], bc[1], bc[2])
        self.c.rect(lowerx_limit * mm, lowery_limit * mm, (upperx_limit-lowerx_limit) * mm, (uppery_limit - lowery_limit) * mm, fill=1, stroke=0)
        self.c.setStrokeColorRGB(col[0] / 255, col[1] / 255, col[2] / 255)
        for x in range(5, upperx_limit+1, 1):
            if (x - 5) % 50 == 0:
                self.c.setLineWidth(0.5 * mm)
            elif not (x - 5) % 10 == 0:
                self.c.setLineWidth(0.2 * mm)
            else:
                self.c.setLineWidth(0.3 * mm)
            self.c.line(x * mm, lowery_limit * mm, x * mm, uppery_limit * mm)

        for x in range(5, uppery_limit + 1, 1):
            if (x - 5) % 50 == 0:
                self.c.setLineWidth(0.5 * mm)
            elif (x - 5) % 10 == 0:
                self.c.setLineWidth(0.3 * mm)
            else:
                self.c.setLineWidth(0.2 * mm)
            self.c.line(lowerx_limit * mm, x * mm, upperx_limit * mm, x * mm)

    def create_point(self, x, y):
        self.c.rect((x - 0.25) * mm, (y - 0.25) * mm, 0.5 * mm, 0.5 * mm, fill=1)

    def adjust_values(self, deg, t, dt, upper_limit=18, lower_limit=9):
        while True:
            min_t = min(t)
            max_t = max(t)
            if upper_limit >= (max_t - min_t) * 5 > lower_limit:
                kx = 5
                break
            elif upper_limit >= (max_t - min_t) * 2 > lower_limit:
                kx = 2
                break
            elif upper_limit >= (max_t - min_t) * 1 > lower_limit:
                kx = 1
                break
            elif upper_limit >= (max_t - min_t) * 4 > lower_limit:
                kx = 4
                break
            elif upper_limit >= (max_t - min_t) * 2.5 > lower_limit:
                kx = 2.5
                break
            else:
                for i in range(len(self.X)):
                    t[i] *= 10
                    dt[i] *= 10
                deg -= 1
        return kx, deg, t, dt

    def create_vertical_grafik(self):

        self.c.setStrokeAlpha(1 - self.conf['opacity'] / 100)
        self.c.setFillAlpha(1 - self.conf['opacity'] / 100)

        ### подгоняем под требования величины

        kx, self.degx, self.X, self.dX = self.adjust_values(self.degx, self.X, self.dX, upper_limit=18, lower_limit=9)
        ky, self.degy, self.Y, self.dY = self.adjust_values(self.degy, self.Y, self.dY, upper_limit=27, lower_limit=14)



        ####### переход в новую систему координат
        self.c.translate(15 * mm, 15 * mm)

        ### оси рисуем

        self.c.setLineWidth(0.5 * mm)
        if not self.D['draw_Y']:
            self.c.line(0 * mm, 0 * mm, 0 * mm, 270 * mm)
            self.draw_triangle_polygon(0, 270, 1)

        if not self.D['draw_X']:
            self.c.line(0 * mm, 0 * mm, 180 * mm, 0 * mm)
            self.draw_triangle_polygon(180, 0, 3)

        ### Проставляем значения и засечки хз как называются


        if not self.D['num_Y'] and not self.D['draw_Y']:
            if not round(min(self.Y)):
                for i in range(26):
                    self.c.drawString(-8 * mm, (9 + 10 * i) * mm, str(round(round(min(self.Y)) + (1 / ky) * (i + 1), 3)))
            else:
                for i in range(26):
                    self.c.drawString(-8 * mm, (9 + 10 * i) * mm, str(round(round(min(self.Y)) + (1 / ky) * i, 3)))

        if not self.D['num_X'] and not self.D['draw_X']:
            if not round(min(self.X)):
                for i in range(17):
                    self.c.drawString((7 + 10 * i) * mm, -5 * mm, str(round(round(min(self.X)) + (1 / kx) * (i + 1), 3)))
            else:
                for i in range(17):
                    self.c.drawString((7 + 10 * i) * mm, -5 * mm, str(round(round(min(self.X)) + (1 / kx) * i, 3)))

        k, l, m = 0, 190, 10
        self.c.setLineWidth(0.2 * mm)

        if not self.D['num_X'] and not self.D['draw_X']:
            while True:
                k += m
                if k == l:
                    break
                self.c.line(k * mm, -1 * mm, k * mm, +1 * mm)

        if not self.D['num_Y'] and not self.D['draw_Y']:
            k, l, m = 0, 270, 10
            while True:
                k += m
                if k == l:
                    break
                self.c.line(-1 * mm, k * mm, 1 * mm, k * mm)

        ### расставляем точечки
        self.rx = []
        self.ry = []
        self.rdx = []
        self.rdy = []
        for i in range(len(self.X)):
            self.create_point((self.X[i] - round(min(self.X))) * kx * 10 + 10 * (0 if not round(min(self.X)) else 1),
                         (self.Y[i] - round(min(self.Y))) * ky * 10 + 10 * (0 if not round(min(self.Y)) else 1))
            self.rx.append((self.X[i] - round(min(self.X))) * kx * 10 + 10 * (0 if not round(min(self.X)) else 1))
            self.ry.append((self.Y[i] - round(min(self.Y))) * ky * 10 + 10 * (0 if not round(min(self.Y)) else 1))
            self.rdx.append(self.dX[i] * kx * 10)
            self.rdy.append(self.dY[i] * kx * 10)


        ### подписываем оси

        # self.c.drawString(184 * mm, 0 * mm, "P")
        if self.D["label_axes"]:
            if not self.D['draw_X']:
                if self.degx != 0:
                    self.c.drawString(176 * mm, -4.4 * mm, f"{self.D['q_2']}, 10{stp(self.degx)},")
                else:
                    self.c.drawString(176 * mm, -4.4 * mm, f"{self.D['q_2']},")
                self.c.drawString(176 * mm, -7.5 * mm, f"{self.D['ed_2']}")

            if not self.D['draw_Y']:
                if self.degy != 0:
                    self.c.drawString(-8 * mm, 275 * mm, f"{self.D['q_1']}, 10{stp(self.degy)},{self.D['ed_1']}")
                else:
                    self.c.drawString(-8 * mm, 275 * mm, f"{self.D['q_1']},{self.D['ed_1']}")

        return self.rx, self.ry, self.rdx, self.rdy

    def create_horizontal_grafik(self):
        self.c.setStrokeAlpha(1 - self.conf['opacity'] / 100)
        self.c.setFillAlpha(1 - self.conf['opacity'] / 100)

        ### подгоняем под требования величины

        kx, self.degx, self.X, self.dX = self.adjust_values(self.degx, self.X, self.dX, upper_limit=27, lower_limit=14)
        ky, self.degy, self.Y, self.dY = self.adjust_values(self.degy, self.Y, self.dY, upper_limit=18, lower_limit=9)



        #######

        self.c.translate(15 * mm, 285 * mm)
        self.c.rotate(270)

        ### оси рисуем

        self.c.setLineWidth(0.5 * mm)
        if not self.D['draw_Y']:
            self.c.line(0 * mm, 0 * mm, 0 * mm, 180 * mm)
            self.draw_triangle_polygon(0, 180, 1)

        if not self.D['draw_X']:
            self.c.line(270 * mm, 0 * mm, 0 * mm, 0 * mm)
            self.draw_triangle_polygon(270, 0, 2)
        ### Проставляем значения и засечки хз как называются

        if not self.D['num_Y'] and not self.D['draw_Y']:
            for i in range(17):
                self.c.drawString(-8 * mm, (9 + 10 * i) * mm,
                             str(round(round(min(self.Y)) + (1 / ky) * (i + (1 if not round(min(self.Y)) else 0)), 3)))
        if not self.D['num_X'] and not self.D['draw_X']:
            for i in range(26):
                self.c.drawString((7 + 10 * i) * mm, -5 * mm,
                             str(round(round(min(self.X)) + (1 / kx) * (i + (1 if not round(min(self.X)) else 0)), 3)))

        k, l, m = 0, 270, 10
        self.c.setLineWidth(0.2 * mm)

        if not self.D['num_X'] and not self.D['draw_X']:
            while True:
                k += m
                if k == l:
                    break
                self.c.line(k * mm, -1 * mm, k * mm, +1 * mm)
        if not self.D['num_Y'] and not self.D['draw_Y']:
            k, l, m = 0, 190, 10
            while True:
                k += m
                if k == l:
                    break
                self.c.line(-1 * mm, k * mm, 1 * mm, k * mm)

        ### расставляем точечки

        self.rx = []
        self.ry = []
        self.rdx = []
        self.rdy = []

        for i in range(len(self.X)):
            self.create_point((self.X[i] - round(min(self.X))) * kx * 10 + 10 * (0 if not round(min(self.X)) else 1),
                         (self.Y[i] - round(min(self.Y))) * ky * 10 + 10 * (0 if not round(min(self.Y)) else 1))
            self.rx.append((self.X[i] - round(min(self.X))) * kx * 10 + 10 * (0 if not round(min(self.X)) else 1))
            self.ry.append((self.Y[i] - round(min(self.Y))) * ky * 10 + 10 * (0 if not round(min(self.Y)) else 1))
            self.rdx.append(self.dX[i] * kx * 10)
            self.rdy.append(self.dY[i] * kx * 10)

        ### подписываем оси

        if self.D['label_axes']:
            if not self.D['draw_X']:
                if self.degx != 0:
                    self.c.drawString(266.5 * mm, -4.4 * mm, f"{self.D['q_2']}, 10{stp(self.degx)},")
                else:
                    self.c.drawString(266.5 * mm, -4.4 * mm, f"{self.D['q_2']},")
                self.c.drawString(266.5 * mm, -7.5 * mm, f"{self.D['ed_2']}")

            if not self.D['draw_Y']:
                if self.degy != 0:
                    self.c.drawString(-8 * mm, 186 * mm, f"{self.D['q_1']}, 10{stp(self.degy)}, {self.D['ed_1']}")
                else:
                    self.c.drawString(-8 * mm, 186 * mm, f"{self.D['q_1']}, {self.D['ed_1']}")
        return self.rx, self.ry, self.rdx, self.rdy


    def draw_errors(self):
        for i in range(len(self.rx)):
            self.c.setLineWidth(0.3 * mm)

            if self.D['x_errors']:
                self.c.line((self.rx[i] - self.rdx[i]) * mm, self.ry[i] * mm, (self.rx[i] + self.rdx[i]) * mm, self.ry[i] * mm)
                self.c.line((self.rx[i] - self.rdx[i]) * mm, (self.ry[i] + 1) * mm, (self.rx[i] - self.rdx[i]) * mm, (self.ry[i] - 1) * mm)
                self.c.line((self.rx[i] + self.rdx[i]) * mm, (self.ry[i] + 1) * mm, (self.rx[i] + self.rdx[i]) * mm, (self.ry[i] - 1) * mm)
            if self.D['y_errors']:
                self.c.line(self.rx[i] * mm, (self.ry[i] - self.rdy[i]) * mm, self.rx[i] * mm, (self.ry[i] + self.rdy[i]) * mm)
                self.c.line((self.rx[i] + 1) * mm, (self.ry[i] - self.rdy[i]) * mm, (self.rx[i] - 1) * mm, (self.ry[i] - self.rdy[i]) * mm)
                self.c.line((self.rx[i] - 1) * mm, (self.ry[i] + self.rdy[i]) * mm, (self.rx[i] + 1) * mm, (self.ry[i] + self.rdy[i]) * mm)
    
    def what_it(self):
        while True:
            if max(self.X) > 1:
                for i in range(len(self.X)):
                    self.X[i] /= 10
                    self.dX[i] /= 10
                self.degx += 1
            else:
                break
        while True:
            if max(self.Y) > 1:
                for i in range(len(self.Y)):
                    self.Y[i] /= 10
                    self.dY[i] /= 10
                self.degy += 1
            else:
                break

    def draw_triangle_polygon(self, x, y, b):
        self.c.setStrokeColorRGB(0, 0, 0)
        self.c.setFillColorRGB(0, 0, 0)
        self.c.setLineWidth(1)
        if b == 1:  ### вертикальная y
            points = [
                x * mm, (y + 3) * mm,
                (x + 0.5) * mm, y * mm,
                (x - 0.5) * mm, y * mm
            ]
        elif b == 2:  ### вертикальная x
            points = [
                (x + 3) * mm, y * mm,
                x * mm, (y + 0.5) * mm,
                x * mm, (y - 0.5) * mm
            ]
        elif b == 3:  ### горизонтальная y
            points = [
                (x + 3) * mm, y * mm,
                x * mm, (y + 0.5) * mm,
                x * mm, (y - 0.5) * mm
            ]
        else:
            points = [
                x * mm, (y - 3) * mm,
                (x + 0.5) * mm, y * mm,
                (x - 0.5) * mm, y * mm
            ]
        p1 = self.c.beginPath()
        p1.moveTo(points[0], points[1])
        p1.lineTo(points[2], points[3])
        p1.lineTo(points[4], points[5])
        p1.close()
        self.c.drawPath(p1, fill=1, stroke=1)

    def graduir(self):

        rxmm = self.rx
        rymm = self.ry
        for i in range(len(rxmm) - 1):
            for j in range(len(rxmm) - 1 - i):
                if rxmm[j] > rxmm[j + 1]:
                    rxmm[j], rxmm[j + 1] = rxmm[j + 1], rxmm[j]
                    rymm[j], rymm[j + 1] = rymm[j + 1], rymm[j]

        for i in range(len(rxmm) - 1):
            self.c.line(rxmm[i] * mm, rymm[i] * mm, rxmm[i + 1] * mm, rymm[i + 1] * mm)

    def naim_qv(self):

        sxy, sy, sx, sx2, n = 0, 0, 0, 0, len(self.rx)

        for i in range(n):
            sxy += self.rx[i] * self.ry[i] * mm * mm
            sy += self.ry[i] * mm
            sx += self.rx[i] * mm
            sx2 += (self.rx[i] * mm) ** 2

        a = (n * sxy - sx * sy) / (n * sx2 - sx ** 2)
        b = (sy - a * sx) / n
        # y = ax+b
        if self.D["orientation"]:

            y2 = 180 * mm * a + b
            x2 = 180 * mm
            if y2 > 280 * mm:
                y2 = 280 * mm
                x2 = (y2 - b) / a
            x1 = 0
            y1 = b
            if y1 < 0:
                y1 = 0
                x1 = -b / a

        else:
            y2 = 280 * mm * a + b
            x2 = 280 * mm
            if y2 > 180 * mm:
                y2 = 180 * mm
                x2 = (y2 - b) / a
            x1 = 0
            y1 = b
            if y1 < 0:
                y1 = 0
                x1 = -b / a

        self.c.line(x1, y1, x2, y2)
        return a, b


    def splain(self):
        rxmm = list(map(lambda s: s * mm, self.rx))
        rymm = list(map(lambda s: s * mm, self.ry))

        for i in range(len(rxmm) - 1):
            for j in range(len(rxmm) - 1 - i):
                if rxmm[j] > rxmm[j + 1]:
                    rxmm[j], rxmm[j + 1] = rxmm[j + 1], rxmm[j]
                    rymm[j], rymm[j + 1] = rymm[j + 1], rymm[j]

        x_original = np.array(rxmm)
        y_original = np.array(rymm)

        cs = CubicSpline(x_original, y_original)

        x_new = np.linspace(x_original.min(), x_original.max(), 300)
        y_new = cs(x_new)

        spline_points = list(zip(x_new, y_new))

        path = self.c.beginPath()
        path.moveTo(spline_points[0][0], spline_points[0][1])
        for x, y in spline_points[1:]:
            path.lineTo(x, y)
        self.c.drawPath(path)
