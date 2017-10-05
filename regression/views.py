import json
import base64
from io import BytesIO

from scipy import stats
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure

from django.shortcuts import render
from django.views import View
from django.http import HttpResponse

class IndexView(View):
	def get(self, request):
		"""
		Type: Public.

		Arguments: HTTP request.

		Return: HttpResponse to render index template.

		Raise: Nothing.

		This method render index.html template
		"""
		return render(request, 'regression/index.html')

class LinerReg(View):
    def post(self, request):
        """
        Type: Public.

        Arguments: HTTP request.

        Return: HttpResponse.

        Raise: Nothing.

        following steps will be performed in this method.
            - get upper limit, lower limit, time and potency data from table.
            - call generate_chart method
            - return HttpResponse with base64 converted chart.
        """
        try:
            up_limit = lw_limit = None
            if request.POST.get('upper_limit'):
                up_limit = float(request.POST.get('upper_limit'))
            if request.POST.get('lower_limit'):
                lw_limit = float(request.POST.get('lower_limit'))
            data = json.loads(request.POST.get('table_data'))
            time = [d['time'] for d in data]
            time = np.array(time).astype(np.float)
            potency = [d['potency'] for d in data]
            potency = np.array(potency).astype(np.float)
            x_label = request.POST.get('time_unit')
            y_label = request.POST.get('value_type')
            chart = self.generate_chart(up_limit, lw_limit, time, potency,
                x_label=x_label, y_label=y_label)
            return HttpResponse(json.dumps({'status':True, 'chart':chart}))
        except Exception as inst:
            print(inst)
            return HttpResponse(json.dumps({'status':False, 'msg': str(inst)}))
        pass

    def generate_chart(self, up_limit, lw_limit, time, potency, **kwargs):
        """
        Type: Public.

        Arguments:
            - up_limit: upper limit value.
            - lw_limit: lower limit value.
            - time: list of time values.
            - potency: list of potency values.

        Return: base64 converted chart image.

        Raise: Nothing.

        following steps will be performed in this method.
            - find linear regression for time and potency values.
            - create matplotlib Figure object.
            - create scatter chart and upper-lower limit lines.
            - create linear regression line.
            - convert matlplotlib image to base64 encoded format.
        """
        slope, intercept, r_value, p_value, std_err = stats.linregress(time, potency)
        fig=Figure()
        ax=fig.add_subplot(111)
        ax.set_xlabel('Time (' + kwargs.get('x_label', '-') +')')
        ax.set_ylabel(kwargs.get('y_label', ''))
        x = np.array(time, dtype=np.float64)
        y = np.array(potency, dtype=np.float64)
        ax.plot(x, slope*x + intercept, color='blue', lw=5)
        ax = self.extended(ax, x, y,  color='blue', label="extended")
        if up_limit:
            ax.plot(x, np.zeros(1)*x + np.array(up_limit, dtype=np.float64), color='red')
        if lw_limit:
            ax.plot(x, np.zeros(1)*x + np.array(lw_limit, dtype=np.float64), color='red')
        ax.scatter(time, potency)
        canvas=FigureCanvas(fig)
        graphic = BytesIO()
        canvas.print_png(graphic)
        return base64.b64encode(graphic.getvalue()).decode("utf-8")

    def extended(self, ax, x, y, **args):
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()
        x_ext = np.linspace(xlim[0], xlim[1], 100)
        p = np.polyfit(x, y , deg=1)
        y_ext = np.poly1d(p)(x_ext)
        ax.plot(x_ext, y_ext, **args)
        # ax.set_xlim(min(x))
        # ax.set_ylim(min(y))
        return ax

		
class Arrhenius(object):
    """
    """
    def __call__(self, time, T, temp_unit='K'):
        from math import exp
        if len(time) != len(T):
            raise ValueError("Time and Temprature must be of equal length.")
        if temp_unit == 'C':
            from scipy.constants import convert_temperature
            T = convert_temperature(T, 'Celsius', 'Kelvin')
        TK = 1000/T
        lnt = np.log(time)
        R = 8.314472
        slope, intercept, r_value, p_value, std_err = stats.linregress(TK, lnt)
        return {'lnt':lnt, 'TK':T, 'TK1000':TK, 'A':slope, 'correlation':r_value}

class ArrheniusView(View):
    """
    """
    def get(self, request):
        """
        """
        return render(request, 'regression/arrhenius.html', {'result':False})

    def post(self, request):
        """
        """
        data = json.loads(request.POST.get('table_data'))
        time = [d['time'] for d in data]
        time = np.array(time).astype(np.float)
        temp = [d['temp'] for d in data]
        temp = np.array(temp).astype(np.float)
        a = Arrhenius()
        data = a(time, temp, temp_unit="C")
        data.update({'time':time.tolist(), 'temp':temp.tolist(), 'result':True})
        time = data.get('time')
        temp = data.get('temp')
        lnt = data.get('lnt').tolist()
        TK = data.get('TK').tolist()
        TK1000 = data.get('TK1000').tolist()
        result_data = []
        length = len(time)
        chart = self.generate_arrhenius_chart(data.get('TK1000'), data.get('lnt'))
        for a, b, c, d, e in zip(time, lnt, temp, TK, TK1000):
            result_data.append({'time':a, 'lnt':b, 'temp':c, 'TK':d, 'TK1000':e,
            'length':length, 'a':data.get('A'), 'correlation':data.get('correlation')})
        return HttpResponse(json.dumps({'status':True, 'calculations':result_data,
            'chart':chart}))

    def generate_arrhenius_chart(self, TK1000, lnt, **kwargs):
        """
        """
        slope, intercept, r_value, p_value, std_err = stats.linregress(TK1000, lnt)
        fig=Figure()
        ax=fig.add_subplot(111)
        ax.set_xlabel('1000K/T')
        ax.set_ylabel('lnt')
        ax.plot(TK1000, slope*TK1000 + intercept, color='blue')
        ax = self.extended(ax, TK1000, lnt,  color='blue', label="extended")
        ax.scatter(TK1000, lnt)
        # y = a0 + A1 X + A2 X^2
        fit = np.polyfit(TK1000, lnt, deg=2)
        print(fit)
        ax.plot(TK1000, fit[2] + fit[1] * TK1000 + fit[0] * np.square(TK1000), color='red')
        canvas=FigureCanvas(fig)
        graphic = BytesIO()
        canvas.print_png(graphic)
        return base64.b64encode(graphic.getvalue()).decode("utf-8")

    def extended(self, ax, x, y, **args):
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()
        x_ext = np.linspace(xlim[0], xlim[1], 100)
        p = np.polyfit(x, y , deg=1)
        y_ext = np.poly1d(p)(x_ext)
        ax.plot(x_ext, y_ext, **args)
        return ax
