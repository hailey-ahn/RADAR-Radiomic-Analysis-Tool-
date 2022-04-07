import pandas as pd
import matplotlib.pyplot as plt
import mpld3


########################
#Create the Python figure
########################

#Set the size of the matplotlib canvas
fig = plt.figure(figsize = (18,8))


#Create the x-axis data
x = [1,2,3,4,5,6,7,8,9,10]

#Create the y-axis data
y = [1,2,3,4,5,6,7,8,9,10]

#Generate the scatterplot
plt.scatter(x, y)

#Add titles to the chart and axes
plt.title("Radiomics Feature")
plt.ylabel("Feature")
plt.xlabel("Tumor size")


################################################
#Save the figure to our local machine
################################################

html_str = mpld3.fig_to_html(fig)
Html_file= open("plot.html","w")
Html_file.write(html_str)
Html_file.close()