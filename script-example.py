from src.interfaces.script import DOMP, POTENTIAL, PROJECTION, Print

with DOMP() as domp:
  ### About

  # print about information
  domp.about()
  
  ### Load and reset projections

  # load a predefined projection
  domp.loadProjection(PROJECTION.Eckert_I)
  # save a screenshot to the `~/Downloads` folder
  domp.screenshot()
  # load another projection
  domp.loadProjection(name='load a projection by its SRID', srid='ESRI:53043')
  # save a screenshot to the `~/Downloads` folder
  domp.screenshot()
  # save the csv data of the  to the `~/Downloads` folder
  domp.data()
  # reset the projection to the initial projection
  domp.loadProjection()

  ### Change simulation settings

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

  ### Saving data, screenshots, and videos

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

  # collect existing data files, concat them, and save them to a new file
  # DOMP.collectData('some-path/*/**/domp-optimization-*.csv', addPath=['new-path'], filename='domp-optimization.csv')

  ### Information

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

  ### View Settings

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
