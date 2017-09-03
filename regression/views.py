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
                up_limit = int(request.POST.get('upper_limit'))
            if request.POST.get('lower_limit'):
                lw_limit = int(request.POST.get('lower_limit'))
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
        #ax = self.extended(ax, x, np.array(potency, np.float64),  color="r", lw=2, label="extended")
        ax.plot(x, slope*x + intercept, color='blue')
        if up_limit:
            ax.plot(x, np.zeros(1)*x + np.array(up_limit, dtype=np.float64), color='red')
        if lw_limit:
            ax.plot(x, np.zeros(1)*x + np.array(lw_limit, dtype=np.float64), color='red')
        ax.scatter(time, potency)
        canvas=FigureCanvas(fig)
        graphic = BytesIO()
        canvas.print_png(graphic)
        return base64.b64encode(graphic.getvalue()).decode("utf-8")
