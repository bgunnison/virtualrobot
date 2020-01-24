"""
visualizes echo exponential delays to improve algorithm
"""
import math
import numpy as np
import pandas as pd
#from plotly.offline import plot
#from plotly.graph_objs import Scatter, Layout
import plotly.express as px

def calc_delays(ticks, echoes):
    new_delays = [0]  # initial note
    delay_start_ticks = ticks
    echoes = echoes

    s = 0.2
    e = 4
    a = (e - s)/float(echoes)
    for i in range(echoes):
        v = 0.2 + ((i+1) * a)
        f = (1.61 + math.log(v))/2.996
        delay = round(delay_start_ticks * f)
        new_delays.append(delay)

    return new_delays

def plot(echoes, start_tick, delays):

    x_axis = np.linspace(0,1,delays[-1])
    label = f'Echos: {echoes}, start tick: {start_tick}'

        #t = np.linspace(0, 10, 100)
    #df = pd.DataFrame({'x':t, 'y':t})
    #fig = px.scatter(df, x='x', y='y',labels={'x':'t', 'y':'t'})

    #t = np.linspace(0, 10, 100)
    #df = pd.DataFrame({'x':t, 'y':t})
    #fig = px.scatter(df, x='x', y='y',labels={'x':'t', 'y':'t'})
    fig.show()

    """
    scatters.append((Scatter(x=delays, y=1)))


    plot(
            {
                "data": scatters,
                "layout": Layout(title=label,
                                xaxis=dict(title='Time'),
                                yaxis=dict(title='note'),
                                annotations=[]),

            },
            show_link=False,
            #filename=label.replace(' ','_') + '.html'
        )
"""

if __name__ == '__main__':
    ticks=24
    echoes=3
    delays = calc_delays(ticks, echoes)
    print(f'Delays: {delays}')
    plot(echoes, ticks, delays)
