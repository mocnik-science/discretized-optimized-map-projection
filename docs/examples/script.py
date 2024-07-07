from src.interfaces.script import DOMP, POTENTIAL, PROJECTION, Print

with DOMP() as domp:
  ### About

  domp.about()
  
  ### Load and reset projections

  # domp.loadProjection(PROJECTION.Eckert_I)
  # domp.screenshot()
  # domp.loadProjection(name='Hurray', srid='ESRI:53043')
  # domp.data()

if False:

  domp.screenshot()

  domp.loadProjection()
  domp.screenshot()

  ### Change simulation settings

  Print(domp.settings())

  domp.resolution(3)
  domp.dampingFactor(.97)
  domp.speed(3)
  Print('speed', domp.speed())
  domp.stopThreshold(maxForceStrength=.1, countDeficiencies=100, maxSteps=5000)
  domp.limitLatForEnergy(90)

  domp.weights(POTENTIAL.AREA, active=False, weightLand=1, weightOceanActive=False, weightOcean=.3, distanceTransitionStart=100, distanceTransitionEnd=800)
  domp.normalizeWeights(normalizeWeights=True)
  domp.saveJSON(domp.weights(), addPart='weights')

  ### Saving data, screenshots, and videos

  ## preventSnapshots=True, preventInitialSnapshot=True

  data = domp.startData()
  video = domp.startVideo()
  domp.steps(n=2)
  data2 = domp.startData()
  domp.steps(n=2)
  domp.stopData(data)
  domp.saveData(data2)
  domp.screenshot()
  domp.screenshot(path='~/Downloads', filename='important.png', largeSymbols=True)
  domp.screenshot(addPath='new-files', addParts=['remember', 'this'])
  domp.saveVideo(video)
  domp.steps(n=2)
  data = domp.appendData(data)
  domp.steps(n=2)
  data = domp.startData(data)
  domp.steps(n=2)
  domp.saveData(data)

  ### Information

  Print(domp.energy())
  Print(domp.energy(inner=False, weighted=False))
  Print(domp.energyPerPotential())
  Print(domp.energyPerPotential(inner=False, weighted=False))
  Print(domp.deficiencies())
  Print(domp.almostDeficiencies())

  ### View Settings

  domp.viewForces()
  domp.viewForces(all=True, sum=True)
  domp.viewForces(potential=POTENTIAL.AREA, sum=False)

  domp.viewEnergy()
  domp.viewEnergy(all=True)
  domp.viewEnergy(potential=POTENTIAL.AREA)

  domp.viewNeighbours()
  domp.viewNeighbours(show=True)

  domp.viewLabels()
  domp.viewLabels(show=True)

  domp.viewSupportingPoints()
  domp.viewSupportingPoints(active=True)
  domp.viewSupportingPoints(weightsForPotential=POTENTIAL.AREA)

  domp.viewOriginalPolygons()
  domp.viewOriginalPolygons(show=True)

  domp.viewContinents(showStronglySimplified=True)
  domp.viewContinents(showSimplified=True)
  domp.viewContinents(showWithTolerance=2)
  domp.viewContinents(show=True)

  domp.viewGraticule(show=True)
  domp.viewGraticule(dDegree=30)
  domp.viewGraticule(degResolution=6)

  DOMP.collectData(pathA + '/*/**/domp-optimization-*.csv', addPath=['path'], filename='domp-optimization.csv')
