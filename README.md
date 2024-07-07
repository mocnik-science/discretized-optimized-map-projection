# Discretized Optimized Map Projection

Projections for world maps can only be a compromise between different requirements as it is impossible to construct a projection that preserves distances, areas, and angles.  Accordingly, choosing a suitable projection is difficult – the wish list of requirements for such a projection is sometimes long and in most cases impossible to fulfil.  This software provides methods to translate such a wish list into a suitable compromise projection.

## Scientific Publications

The theoretical underpinnings of this software, including a description of the mechanisms used to translate the wish list of requirements to a projection, can be found here:

* FB Mocnik: [**Compromise Projections for World Maps – An Optimization Approach Using Discrete Global Grid Systems and Principles From Classical Mechanics**](https://doi.org/10.1080/17538947.2024.2369636).  International Journal of Digital Earth, 2024.  doi:10.1080/17538947.2024.2369636

## Short Overview

### Installation

To install the software, you will need `git`, `python3`, and `pip` ([How to install pip](https://pip.pypa.io/en/stable/installing/)).

First, you have to clone the software:
```bash
git clone https://github.com/mocnik-science/discretized-optimized-map-projection.git
cd discretized-optimized-map-projection
chmod 755 run.py
```
Then, install the dependencies:
```bash
pip install .
```
On some operating systems, `pip` for `python3` is named `pip3`:
```bash
pip3 install .
```

### Application

To run the software as an application with a GUI, execute the following:
```bash
./run.py
```

The main window will be displayed:
<p align="center"><img src="/docs/images/window-main.jpg" width="80%"/></p>

The simulation settings window can be used to display and adapt the wish list of requirements to the projection:
<p align="center"><img src="/docs/images/window-simulation-settings.jpg" width="80%"/></p>

When the final projection is found, it can be exported to [QGIS](https://www.qgis.org):
<p align="center"><img src="/docs/images/window-projections-qgis.jpg" width="80%"/></p>

Numerous options are provided in the menus to customize the display of the projection and export it in image and video format, or as a tinshift projection that can be read by QGIS.

<table>
  <tr>
    <th>Projection Menu</th>
    <th>Caption Menu</th>
  </tr>
  <tr>
    <td align="center" valign="top"><img src="/docs/images/menu-projection.jpg" width="80%"/></td>
    <td align="center" valign="top"><img src="/docs/images/menu-capture.jpg" width="80%"/></td>
  </tr>  
</table>

<table>
  <tr>
    <th>Simulation Menu</th>
    <th>View Menu</th>
  </tr>
  <tr>
    <td align="center" valign="top"><img src="/docs/images/menu-simulation.jpg" width="80%"/></td>
    <td align="center" valign="top"><img src="/docs/images/menu-view.jpg" width="80%"/></td>
  </tr>  
</table>

### Scripting

The software provides a scripting interface whose scope is comparable to that of the GUI.

The software can be loaded as:
```python
from src.interfaces.script import DOMP, POTENTIAL, PROJECTION, Print

with DOMP() as domp:
  ...
```
Inside the with clause, the object `domp` (Discretized Optimized Map Projection) is available and offers the methods needed to create, render, and export projections.  Please note that the script needs to be run in the root folder of this repository to allow for the import of DOMP.

To test the functionality, you can execute:
```python
# print about information
domp.about()
```
A corresponding message will appear in the command line.  You can proceed with loading projections:
```python
# load a pre-defined projection
domp.loadProjection(PROJECTION.Eckert_I)
# save a screenshot to the `~/Downloads` folder
domp.screenshot()
# load another projection
domp.loadProjection(name='load a projection by its SRID', srid='ESRI:53043')
# save a screenshot to the `~/Downloads` folder
domp.screenshot()
```
In case the initial projection has been optimized (which will be discussed later), you can save the corresponding data of the optimization (such as the remaining energy per step) and reset the projection like follows:
```python
# save the csv data of the  to the `~/Downloads` folder
domp.data()
# reset the projection to the initial projection
domp.loadProjection()
```
Before running the optimization of the projection, you can adjust the simulation/optimization settings, which include the wish list of requirements to the projection.
```python
# print the current settings
Print(domp.settings())
# adjust the settings
domp.resolution(3)
domp.dampingFactor(.97)
domp.speed(3)
# print the setting
Print('speed', domp.speed())
# adjust the threshold when to stop the simulation
domp.stopThreshold(maxForceStrength=.1, countDeficiencies=100, maxSteps=5000)
# only compute the energy for cells within a certain latitude range
domp.limitLatForEnergy(90)
# adjust the weights
domp.weights(POTENTIAL.AREA, active=False, weightLand=1, weightOceanActive=False, weightOcean=.3, distanceTransitionStart=100, distanceTransitionEnd=800)
# normalize the weights
domp.normalizeWeights(normalizeWeights=True)
# save the weights to a json file
domp.saveJSON(domp.weights(), addPart='weights')
```
You can optimize the projection by computing it step by step:
```python
# compute one step
domp.steps(n=1)
# compute five step
domp.steps(n=5)
```
There are several commands available to start the data or video collection, and then save corresponding files after the optimization.  For instance, you can run:
```python
# start data collection (data will automatically be captured)
data = domp.startData()
# in some cases, you want to start the data collection without capturing (initial) snapshots automatically
# data = domp.startData(preventInitialSnapshot=True, preventSnapshots=True)
# start video collection (frames will automatically be captured)
video = domp.startVideo()
# compute steps
domp.steps(n=2)
# start another data collection
data2 = domp.startData()
# compute steps
domp.steps(n=2)
# stop the first data collection (usually not necessary)
domp.stopData(data)
# stops and saves the data of the second data collection
domp.saveData(data2)
# take a screenshot
domp.screenshot()
# take a screenshot, with the path and filename explicitly set, and with large symbols in the screenshot
domp.screenshot(path='~/Downloads', filename='important.png', largeSymbols=True)
# take a screenshot, with a subpath and parts (*-test-only) to be added to the filename provided
domp.screenshot(addPath='new-files', addParts=['test', 'only'])
# save the video collection
domp.saveVideo(video)
# compute steps
domp.steps(n=2)
# append another row to the data collection (only for the data since the last stop or save command)
domp.appendData(data, additionalData={'row': 'content'})
# compute steps
domp.steps(n=2)
# stops and saves the data of the second data collection
domp.saveData(data2)
```
In rare cases, you might want to concat several CSV files resulting from differnet optimization processes.  You can collect corresponding files and save them to a new file:
Finally, 
```python
# collect existing data files, concat them, and save them to a new file
DOMP.collectData('some-path/*/**/domp-optimization-*.csv', addPath=['new-path'], filename='domp-optimization.csv')
```
You can easily access and print information related to the current stage of the optimization process:
```python
# inner energy
Print(domp.energy())
# outer energy, without using the weights
Print(domp.energy(inner=False, weighted=False))
# inner energy per potential
Print(domp.energyPerPotential())
# outer energy per potential, without using the weights
Print(domp.energyPerPotential(inner=False, weighted=False))
# number of deficiencies
Print(domp.deficiencies())
# number of almost deficiencies
Print(domp.almostDeficiencies())
```
You can at any time adjust the render settings, which are used in the images and the videos:
```python
# resets to default: all=False, potential=None, sum=True
domp.viewForces()
# adjusted settings
domp.viewForces(all=True, sum=True)
domp.viewForces(potential=POTENTIAL.AREA, sum=False)

# resets to default: all=False, potential=None
domp.viewEnergy()
# adjusted settings
domp.viewEnergy(all=True)
domp.viewEnergy(potential=POTENTIAL.AREA)

# resets to default: show=False
domp.viewNeighbours()
# adjusted settings
domp.viewNeighbours(show=True)

# resets to default: show=False
domp.viewLabels()
# adjusted settings
domp.viewLabels(show=True)

# resets to default: active=False, weightsForPotential=None
domp.viewSupportingPoints()
# adjusted settings
domp.viewSupportingPoints(active=True)
domp.viewSupportingPoints(weightsForPotential=POTENTIAL.AREA)

# resets to default: show=False
domp.viewOriginalPolygons()
# adjusted settings
domp.viewOriginalPolygons(show=True)

# resets to default: showStronglySimplified=False, showSimplified=False, show=False, showWithTolerance=None
domp.viewContinents()
# adjusted settings
domp.viewContinents(showStronglySimplified=True)
domp.viewContinents(showSimplified=True)
domp.viewContinents(showWithTolerance=2)
domp.viewContinents(show=True)

# resets to default: show=False, dDegree=20, degResolution=6
domp.viewGraticule()
# adjusted settings
domp.viewGraticule(show=True)
domp.viewGraticule(dDegree=30)
domp.viewGraticule(degResolution=6)
```

The [`script-example.py`](/script-example.py) can be found in the root folder of this repository.  To execute it, run the following command in the root folder:
```bash
python3 script-example.py
```

## Author

This software is written and maintained by Franz-Benjamin Mocnik, <mail@mocnik-science.net>.

(c) by Franz-Benjamin Mocnik, 2023–2024.

## License

The code is licensed under the [MIT license](https://github.com/mocnik-science/discretized-optimized-map-projection/blob/master/LICENSE).
