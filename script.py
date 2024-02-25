#!/usr/bin/env python3

import altair as alt
import csv
from multiprocess import Pool
import os
import pandas as pd
import subprocess

from src.interfaces.script import DOMP, POTENTIAL, PROJECTION, Print

PARALLELIZE = True

ACTION_A = True
ACTION_B = True

CREATE_DATA = False
CREATE_VISUALIZATION = True

TESTING = False

pathA = 'A-optimization'
pathB = 'B-comparison-of-projections'
join = lambda *paths: os.path.expanduser(os.path.join('~', 'Downloads', *paths))

### SETTINGS
def defaultSettings(domp):
  domp.resolution(3)
  domp.speed(4)
  domp.stopThreshold(maxForceStrength=.1 if not TESTING else .4, countDeficiencies=100, maxSteps=5000 if not TESTING else 500)
  domp.limitLatForEnergy(90)

def defaultView(domp):
  domp.viewForces(all=False)
  domp.viewEnergy(all=False)
  domp.viewNeighbours(show=False)
  domp.viewLabels(show=False)
  domp.viewSupportingPoints(active=False, weightsForPotential=None)
  domp.viewOriginalPolygons(show=False)
  domp.viewContinents(show=False)

def defaultWeights(domp):
  domp.weights(POTENTIAL.AREA, active=True, weightLand=1, weightOceanActive=True, weightOcean=.3, distanceTransitionStart=100, distanceTransitionEnd=800)
  domp.weights(POTENTIAL.DISTANCE, active=True, weightLand=1, weightOceanActive=True, weightOcean=.3, distanceTransitionStart=100, distanceTransitionEnd=800)
  domp.weights(POTENTIAL.DISTANCE_HOMOGENEITY, active=False, weightLand=.2, weightOceanActive=True, weightOcean=.05, distanceTransitionStart=100, distanceTransitionEnd=800)
  domp.weights(POTENTIAL.SHAPE, active=False, weightLand=.7, weightOceanActive=True, weightOcean=.3, distanceTransitionStart=100, distanceTransitionEnd=800)
  domp.weights(POTENTIAL.ORIENTATION, active=False, weightLand=.1, weightOceanActive=False, weightOcean=.1, distanceTransitionStart=100, distanceTransitionEnd=800)
  domp.weights(POTENTIAL.TRIANGLE_ALTITUDE, active=True, weightLand=1, weightOceanActive=False, weightOcean=.3, distanceTransitionStart=100, distanceTransitionEnd=800)

def distanceWeights(domp):
  domp.weights(POTENTIAL.DISTANCE, active=True, weightLand=1.7, weightOceanActive=False)
  domp.weights(POTENTIAL.AREA, active=True, weightLand=.3, weightOceanActive=False)

def areaWeights(domp):
  domp.weights(POTENTIAL.AREA, active=True, weightLand=1.7, weightOceanActive=False)
  domp.weights(POTENTIAL.DISTANCE, active=True, weightLand=.3, weightOceanActive=False)

def init(domp):
  defaultSettings(domp)
  defaultView(domp)
  defaultWeights(domp)

### PARALLELIZE
def parallelize(action, projections):
  if PARALLELIZE:
    with Pool() as pool:
      pool.map(action, projections)
  else:
    [action(projection) for projection in projections]

### A: OPTIMIZATION
if CREATE_DATA:
  DOMP.about()
  
  def actionA(projection):
    with DOMP(cleanup=False, logging=not parallelize, hideAbout=True) as domp:
      init(domp)
      data = domp.startData(preventSnapshots=True)
      for i, context in enumerate(['supporting-points-forces-all', 'supporting-points-forces-all-individual', 'neighbours-land']):
        # view settings
        parts = []
        if context == 'supporting-points-forces-all':
          parts = ['supporting-points', 'forces', 'all']
          domp.viewSupportingPoints(active=True)
          domp.viewForces(all=True, sum=True)
        if context == 'supporting-points-forces-all-individual':
          parts = ['supporting-points', 'forces', 'all', 'individual']
          domp.viewSupportingPoints(active=True)
          domp.viewForces(all=True, sum=False)
        if context == 'neighbours-land':
          parts = ['neighbours', 'land']
          domp.viewNeighbours(show=True)
          domp.viewContinents(show=not TESTING, showStronglySimplified=TESTING)
        # run
        domp.limitLatForEnergy(90 if projection != PROJECTION.Mercator else 85.06)
        domp.loadProjection(projection)
        video = domp.startVideo()
        if i == 0:
          domp.startData(dataData=data)
        domp.steps()
        if i == 0:
          domp.stopData(dataData=data)
        domp.saveVideo(video, addPaths=[pathA, projection.name], addParts=parts)
        # reset view settings
        domp.viewSupportingPoints(active=False)
        domp.viewNeighbours(show=False)
        domp.viewContinents(show=False)
        domp.viewForces(all=False)
      domp.saveData(data, addPaths=[pathA, projection.name], filename='domp-optimization-' + projection.name + '.csv')

  if ACTION_A:
    parallelize(actionA, PROJECTION.canBeOptimizedProjections)
    DOMP.collectData(pathA + '/*/**/domp-optimization-*.csv', addPath=pathA, filename='domp-optimization.csv')

  ### B: COMPARISON OF PROJECTIONS
  def actionB(projection):
    with DOMP(cleanup=False, logging=not parallelize, hideAbout=True) as domp:
      init(domp)

      def _screenshot(projection, *parts):
        for extension in ['png', 'svg']:
          filename = domp.screenshot(addPaths=[pathB, projection.name], addParts=parts, extension=extension)
          if extension == 'svg':
            path, fname = os.path.split(filename)
            subprocess.run(f'zip -9 "{fname}.zip" "{fname}" && rm "{fname}"', shell=True, cwd=path, capture_output=True)
      
      def _dump(data, projection, parts, initial=False):
        potentials = [POTENTIAL.DISTANCE, POTENTIAL.AREA, POTENTIAL.TRIANGLE_ALTITUDE]
        # data
        domp.appendData(data, additionalData={'case': '-'.join(parts)})
        if initial and projection.canBeOptimized:
          # initial polygons
          if initial:
            domp.viewOriginalPolygons(show=True)
            _screenshot(projection, 'initial-polygons', *parts)
            domp.viewOriginalPolygons(show=False)
        # supporting points
        domp.viewSupportingPoints(active=True)
        _screenshot(projection, 'supporting-points', *parts)
        # supporting points with labels
        domp.viewLabels(show=True)
        _screenshot(projection, 'supporting-points-with-labels', *parts)
        domp.viewLabels(show=False)
        domp.viewSupportingPoints(active=False)
        if projection.canBeOptimized:
          # neighbours
          domp.viewNeighbours(show=True)
          _screenshot(projection, 'neighbours', *parts)
          domp.viewNeighbours(show=False)
          # forces
          domp.viewForces(all=True, sum=True)
          _screenshot(projection, 'forces', 'all', *parts)
          domp.viewForces(all=True, sum=False)
          _screenshot(projection, 'forces', 'all', 'individual', *parts)
          for potential in potentials:
            domp.viewForces(potential=potential, sum=True)
            _screenshot(projection, 'forces', potential.lower(), *parts)
            domp.viewForces(potential=potential, sum=False)
            _screenshot(projection, 'forces', potential.lower(), 'individual', *parts)
          domp.viewForces(all=False, potential=None)
        # energies
        domp.viewEnergy(all=True)
        _screenshot(projection, 'energies', 'all', *parts)
        for potential in potentials:
          domp.viewEnergy(potential=potential)
          _screenshot(projection, 'energies', potential.lower(), *parts)
        domp.viewEnergy(all=False, potential=None)
        # land
        domp.viewContinents(show=True)
        _screenshot(projection, 'land', *parts)
        domp.viewContinents(show=False)

      def _runComparison(part):
        domp.limitLatForEnergy(90 if projection != PROJECTION.Mercator else 85.06)
        data = domp.startData(preventSnapshots=True)
        for considerLand in [False, True]:
          # weights
          domp.weights(POTENTIAL.AREA, weightOceanActive=considerLand)
          domp.weights(POTENTIAL.DISTANCE, weightOceanActive=considerLand)
          # run
          parts = [part] + (['land'] if considerLand else [])
          domp.loadProjection(projection)
          _dump(data, projection, parts, initial=True)
          if projection.canBeOptimized:
            domp.steps(100)
            _dump(data, projection, parts)
            domp.steps()
            _dump(data, projection, parts)
          # reset weights
          domp.weights(POTENTIAL.AREA, weightOceanActive=True)
          domp.weights(POTENTIAL.DISTANCE, weightOceanActive=True)
        domp.saveData(data, addPaths=[pathB, projection.name], filename='domp-comparison-of-projections-' + part + '.csv')

      # defaultWeights(domp)
      _runComparison('default')

      defaultWeights(domp)
      distanceWeights(domp)
      _runComparison('distance-1.7')

      defaultWeights(domp)
      areaWeights(domp)
      _runComparison('area-1.7')

  if ACTION_B:
    parallelize(actionB, PROJECTION.allProjections)
    DOMP.collectData(pathB + '/*/**/domp-comparison-of-projections-*.csv', addPath=pathB, filename='domp-comparison-of-projections.csv')

### CREATE VISUALIZATIONS
if CREATE_VISUALIZATION:
  factorEnergy = 1e8
  factorEnergyStr = ' [10^8]'
  factorEnergyTransform = {'energyWeighted': 'datum.energyWeighted / ' + str(factorEnergy)}
  stepsMax = 219
  config = {
    'font': 'Helvetica Neue',
  }
  configAxisWithGrid = {
    'labelBound': 40,
    'domainColor': '#888',
    'domainOpacity': 1,
    'tickColor': '#888',
    'tickOpacity': 1,
  }
  configAxis = {
    **configAxisWithGrid,
    'grid': False,
  }
  configView = {
    'stroke': '#888',
    'strokeOpacity': 1,
  }
  labelExprCase = 'datum.label == \'default\' ? \'default\' : datum.label == \'default-land\' ? \'default (land)\' : datum.label == \'distance-1.7\' ? \'distance\' : datum.label == \'distance-1.7-land\' ? \'distance (land)\' : datum.label == \'area-1.7\' ? \'area\' : datum.label == \'area-1.7-land\' ? \'area (land)\' : \'-\''
  domainCase = ['default', 'default-land', 'distance-1.7', 'distance-1.7-land', 'area-1.7', 'area-1.7-land']
  domainCaseLand = ['default-land', 'distance-1.7-land', 'area-1.7-land']
  domainCaseNoLand = ['default', 'distance-1.7', 'area-1.7']
  rangeCase = ['circle', 'circle', 'triangle', 'triangle', 'square', 'square']
  rangeCaseLandNoLand = ['circle', 'triangle', 'square']
  domainLand = ['default', 'default-land', 'distance-1.7', 'distance-1.7-land', 'area-1.7', 'area-1.7-land']
  rangeLand = 3 * ['#1f77b4', '#ff7f0e']
  ### A: OPTIMIZATION
  if ACTION_A:
    filename = join(pathA, 'domp-optimization.csv')
    if os.path.exists(filename):
      data = None
      dataRestricted = None
      energiesInner = ['innerEnergyWeighted', 'innerEnergyWeighted_DISTANCE', 'innerEnergyWeighted_AREA', 'innerEnergyWeighted_TRIANGLE_ALTITUDE']
      energiesOuter = ['outerEnergyWeighted', 'outerEnergyWeighted_DISTANCE', 'outerEnergyWeighted_AREA', 'outerEnergyWeighted_TRIANGLE_ALTITUDE']
      with open(filename) as f:
        # data preparation
        rows = [row for row in csv.DictReader(f)]
        for row in rows:
          for energy in [*energiesInner, *energiesOuter]:
            row[energy] = float(row[energy]) / factorEnergy
          row['outerInnerEnergyWeighted'] = row['outerEnergyWeighted'] / row['innerEnergyWeighted']
          row['step'] = int(row['step'])
        data = pd.DataFrame(rows)
      ## CHART A/01
      # alt.data_transformers.disable_max_rows()
      domainEnd = 3.05 * stepsMax
      for forPrint in [False, True]:
        axis = alt.Axis(grid=False)
        base = alt.Chart(data)
        if forPrint:
          base = base.encode(
            color=alt.value('black'),
            strokeWidth=alt.value(1),
            detail='initialProjectionName:N',
          )
        else:
          base = base.encode(
            color=alt.Color('initialProjectionName:N', legend=None).scale(scheme='category10'),
          )
        chartLine = base.mark_line(clip=True).encode(
          x=alt.X('step:Q', title='step').scale(domain=(0, domainEnd)),
          y=alt.Y('innerEnergyWeighted:Q', axis=axis, title='inner energy' + factorEnergyStr).scale(domain=(0, 1.05e9 / factorEnergy)),
          opacity=alt.value(.5),
        )
        chartLabel = base.mark_text(align='left', dx=5).encode(
          x=alt.X('step:Q', aggregate='max').scale(domain=(0, domainEnd)),
          y=alt.Y('innerEnergyWeighted:Q', aggregate='min'),
          text=alt.Text('initialProjectionName'),
        )
        (chartLine if forPrint else chartLine + chartLabel).configure(
          **config,
        ).configure_axis(
          **configAxis,
        ).configure_view(
          **configView,
        ).transform_filter(
          alt.datum.step < domainEnd
        ).properties(
          width=620,
          height=180,
        ).save(join(pathA, 'chart-a01' + ('' if forPrint else 'b') + '.pdf'))
      ## CHART A/02/legend
      data2Projections = ['Mercator', 'Gall-Peters', 'Natural Earth', 'Aitoff']
      data2 = data.copy()
      data2 = data2[data2['initialProjectionName'].isin(data2Projections)]
      base = alt.Chart(data2).mark_line().encode(
        x=alt.value(0),
        y=alt.value(0),
        color=alt.Color('initialProjectionName:N', legend=alt.Legend(
          orient='none',
          legendX=0,
          legendY=0,
          direction='horizontal',
          symbolType='stroke',
          symbolOpacity=1,
        )).scale(scheme='category10'),
      ).configure(
        **config,
      ).configure_axis(
        **configAxis,
      ).configure_view(
        **configView,
      ).configure_legend(
        title=None,
      ).configure_view(
        stroke=None,
      ).transform_filter(
        alt.datum.step == 0
      ).properties(
        width=1,
        height=1,
      ).save(join(pathA, 'chart-a02-legend.pdf'))
      ## CHART A/02
      def markNonNullValues(column):
        data3 = data2.sort_values(['initialProjectionName', 'step'])
        data3[column] = data3[column].apply(pd.to_numeric)
        data3['prev'] = data3[column].shift(1)
        data3['next'] = data3[column].shift(-1)
        data3['prevProj'] = data3['initialProjectionName'].shift(1)
        data3['nextProj'] = data3['initialProjectionName'].shift(-1)
        def valuesForRow(row, column):
          values = [row[column]]
          if row.initialProjectionName == row['prevProj']:
            values.append(row['prev'])
          if row.initialProjectionName == row['nextProj']:
            values.append(row['next'])
          return [value for value in values if value is not None]
        data3['min_' + column] = data3.apply(lambda row: min(valuesForRow(row, column)), axis=1)
        data3['max_' + column] = data3.apply(lambda row: max(valuesForRow(row, column)), axis=1)
        data3['max_prev'] = data3['max_' + column].shift(1)
        data3['max_next'] = data3['max_' + column].shift(-1)
        data3['keep_' + column] = (data3['max_' + column] > 0) | ((data3.max_prev > 0) & (data3.initialProjectionName == data3.prevProj)) | ((data3.max_next > 0) & (data3.initialProjectionName == data3.nextProj))
        del data3['prev']
        del data3['next']
        del data3['prevProj']
        del data3['nextProj']
        del data3['max_prev']
        del data3['max_next']
        return data3
      data2 = markNonNullValues('countDeficiencies')
      data2 = markNonNullValues('countAlmostDeficiencies')
      minExtent = 25
      scaleX = alt.Scale(domain=(0, stepsMax))
      for forPrint in [False, True]:
        base = alt.Chart(data2).encode(
          x=alt.X('step:Q', axis=alt.Axis(labels=False, title=None)).scale(scaleX),
          color=alt.Color('initialProjectionName:N', legend=None if forPrint else alt.Legend(
            orient='none',
            legendX=5.5, # 11 / 2
            legendY=-17,
            direction='horizontal',
            symbolType='stroke',
            symbolOpacity=1,
            # orient='none',
            # legendX=200,
            # legendY=315, # 'f' an Kante + 5.7,
          )).scale(scheme='category10'),
        )
        chartEnergy = base.mark_line(clip=True).transform_fold(
          fold=['innerEnergyWeighted', 'outerEnergyWeighted'],
          as_=['energyWeightedType', 'energyWeighted'],
        ).encode(
          y=alt.Y('energyWeighted:Q', axis=alt.Axis(minExtent=minExtent), title='energy' + factorEnergyStr).scale(domain=(0, 1e9 / factorEnergy)),
          strokeDash=alt.StrokeDash('energyWeightedType:N', legend=alt.Legend(labelExpr='replace(datum.label, \'EnergyWeighted\', \'\')')),
        ).properties(
          width=280,
          height=180,
        )
        chartInnerOuterEnergy = base.mark_line(clip=True).encode(
          y=alt.Y('outerInnerEnergyWeighted:Q', axis=alt.Axis(minExtent=minExtent), title='outer / inner energy').scale(domain=(1.1, 1.55)),
        ).properties(
          width=280,
          height=100,
        )
        baseDeficiencies = base.mark_line(clip=True, interpolate='basis')
        baseDeficienciesArea = base.mark_area(clip=True, interpolate='basis', opacity=.5)
        propertiesAlmostDeficiencies = {
          'width': 280,
          'height': 90,
        }
        propertiesDeficiencies = {
          **propertiesAlmostDeficiencies,
          'height': 45,
        }
        chartAlmostDeficienciesMaxs = []
        x = alt.X('step:Q', axis=None).scale(scaleX)
        y = alt.Y('max_countAlmostDeficiencies:Q', axis=alt.Axis(minExtent=minExtent), title='almost def.').scale(domain=(0, 40))
        for proj in data2Projections:
          chartAlmostDeficienciesMaxs.append(baseDeficiencies.encode(
            x=x,
            y=y,
          ).transform_filter(
            (alt.datum.keep_countAlmostDeficiencies) & (alt.datum.initialProjectionName == proj)
          ).properties(**propertiesAlmostDeficiencies))
        chartAlmostDeficienciesArea = baseDeficienciesArea.encode(
          x=x,
          y=y,
          y2='max_countAlmostDeficiencies:Q',
        ).transform_filter(
          alt.datum.keep_countAlmostDeficiencies
        ).properties(**propertiesAlmostDeficiencies)
        chartDeficienciesMaxs = []
        x = alt.X('step:Q', axis=alt.Axis(labels=True, labelAlign='center', title=None, orient='bottom')).scale(scaleX)
        y = alt.Y('max_countDeficiencies:Q', axis=alt.Axis(minExtent=minExtent), title='full def.').scale(domain=(0, 20), reverse=True)
        for proj in data2Projections:
          chartDeficienciesMaxs.append(baseDeficiencies.encode(
            x=x,
            y=y,
          ).transform_filter(
            (alt.datum.keep_countDeficiencies) & (alt.datum.initialProjectionName == proj)
          ).properties(**propertiesDeficiencies))
        chartDeficienciesArea = baseDeficienciesArea.encode(
          x=x,
          y=y,
          y2='max_countDeficiencies:Q',
        ).transform_filter(
          alt.datum.keep_countDeficiencies
        ).properties(**propertiesDeficiencies)
        # chartDeficiencies = baseDeficiencies.encode(
        #   x=alt.X('step:Q', axis=alt.Scale(), title='step').scale(scaleX),
        #   y=alt.Y('countDeficiencies:Q', axis=alt.Axis(minExtent=minExtent), title='full def.').scale(domain=(0, 20), reverse=True),
        # ).transform_filter(
        #   alt.datum.keep_countDeficiencies
        # ).properties(
        #   width=280,
        #   height=45,
        # )
        # chartDeficiencies = base.mark_line().transform_fold(
        #   fold=['countDeficiencies', 'countAlmostDeficiencies'],
        #   as_=['countType', 'count'],
        # ).encode(
        #   x=alt.X('step:Q', axis=alt.Scale(), title='step').scale(scaleX),
        #   y=alt.Y('count:Q', title='deficiencies'),
        #   opacity=alt.Opacity('countType:N', legend=alt.Legend(
        #     labelExpr='datum.label == \'countAlmostDeficiencies\' ? \'almost deficiencies\' : datum.label == \'countDeficiencies\' ? \'deficiencies\' : \'-\'',
        #     orient='none',
        #     legendX=174.1,
        #     legendY=315, # 'f' an Kante + 5.0,
        #   )),
        # ).transform_filter(
        #   alt.datum.count > 0
        # ).properties(
        #   width=280,
        #   height=180,
        # )
        alt.vconcat(
          chartEnergy,
          chartInnerOuterEnergy,
          alt.vconcat(
            chartAlmostDeficienciesArea + alt.layer(*chartAlmostDeficienciesMaxs),
            chartDeficienciesArea + alt.layer(*chartDeficienciesMaxs),
            bounds='flush',
            spacing=0,
          ),
          bounds='flush',
          spacing=10,
        ).resolve_scale(
          strokeDash='independent',
        ).configure(
          **config,
        ).configure_axis(
          **configAxis,
        ).configure_view(
          **configView,
        ).configure_legend(
          title=None,
          orient='top-right',
          offset=5,
        ).save(join(pathA, 'chart-a02' + ('' if forPrint else 'b') + '.pdf'))
      ## CHART A/03
      scaleX = alt.Scale(domain=(0, stepsMax))
      minExtent = 25
      energiesOuterSubset = {
        'overall energy': 'outerEnergyWeighted',
        'distance energy': 'outerEnergyWeighted_DISTANCE',
        'area energy': 'outerEnergyWeighted_AREA',
      }
      for forPrint in [False, True]:
        base = alt.Chart(data2).encode(
          color=alt.Color('initialProjectionName:N', legend=None if forPrint else alt.Legend()).scale(scheme='category10'),
        )
        chartEnergies = []
        for i, (energyName, energy) in enumerate(energiesOuterSubset.items()):
          chartEnergies.append(base.mark_line(clip=True).encode(
            x=alt.X('step:Q', axis=alt.Axis(labels=(i == len(energiesOuterSubset) - 1), labelAlign='center', title=None)).scale(scaleX),
            y=alt.Y(energy + ':Q', axis=alt.Axis(minExtent=minExtent), title=energyName + factorEnergyStr).scale(domain=(0, 1e9 / factorEnergy)),
          ).properties(
            width=280,
            height=415/3,
          ))
        alt.vconcat(
          *chartEnergies,
          bounds='flush',
          spacing=10,
        ).configure(
          **config,
        ).configure_axis(
          **configAxis,
        ).configure_view(
          **configView,
        ).configure_legend(
          title=None,
          orient='top-right',
          offset=5,
        ).save(join(pathA, 'chart-a03' + ('' if forPrint else 'b') + '.pdf'))
  ### B: COMPARISON OF PROJECTIONS
  if ACTION_B:
    filename = join(pathB, 'domp-comparison-of-projections.csv')
    if os.path.exists(filename):
      data = None
      with open(filename) as f:
        # data preparation
        rows = [row for row in csv.DictReader(f)]
        for row in rows:
          row['innerEnergyWeighted'] = float(row['innerEnergyWeighted']) / factorEnergy
          row['outerEnergyWeighted'] = float(row['outerEnergyWeighted']) / factorEnergy
          row['outerInnerEnergyWeighted'] = row['outerEnergyWeighted'] / row['innerEnergyWeighted']
        data = pd.DataFrame(rows)
        data = data[data['initialProjectionName'] != 'Mercator']
        data = data[~data['initialProjectionName'].str.endswith(' (PROJ)')]
        data['steps'] = data['step'].apply(lambda step: int(step) if step in ['0', '100'] else 'threshold')
        data = data.sort_values(by=['case', 'initialProjectionName'])
      ## CHART B/01
      dataTmp = data.copy()
      dataTmp['innerEnergyWeighted0'] = data.apply(lambda row: row['innerEnergyWeighted'] if row['steps'] == 0 else None, axis=1).apply(pd.to_numeric)
      dataTmp['innerEnergyWeightedThreshold'] = data.apply(lambda row: row['innerEnergyWeighted'] if row['steps'] == 'threshold' else None, axis=1).apply(pd.to_numeric)
      dataGrouped = dataTmp.groupby(['initialProjectionName', 'case']).aggregate({'innerEnergyWeighted0': 'first', 'innerEnergyWeightedThreshold': 'first'})
      dataGrouped = pd.DataFrame(dataGrouped.to_records())
      axis = alt.Axis(grid=False)
      widthHeightChart = 120
      plotDiagonal = alt.Chart().mark_rule(color='gray', strokeWidth=1).encode(
        x=alt.value(.5),
        y=alt.value(widthHeightChart + .5),
        x2=alt.value(widthHeightChart + .5),
        y2=alt.value(.5),
        opacity=alt.value(.1),
      )
      def createDictProjectionsM():
        dictProjectionsM = []
        for projection in dataGrouped['initialProjectionName'].unique():
          if projection == 'unprojected':
            continue
          dictProjectionsM.append((projection, max(*[dataGrouped[dataGrouped['initialProjectionName'] == projection][axisName].dropna().max() for axisName in ['innerEnergyWeighted0', 'innerEnergyWeightedThreshold']])))
        dictProjectionsM.sort(key=lambda x: x[1])
        return dictProjectionsM
      def configPlot(plot, deltaLegendY=0):
        return plot.configure(
          **config,
        ).configure_axis(
          **configAxis,
          minExtent=18,
        ).configure_axisX(
          offset=-3,
        ).configure_axisY(
          offset=-2,
        ).configure_view(
          **configView,
        ).configure_legend(
          title=None,
          orient='none',
          legendX=513,
          legendY=266 + deltaLegendY,
        )
      def createPlot(include, avoid=None, showAxisLabel=True):
        dsGrouped = dataGrouped.copy()
        if avoid:
          dsGrouped = dsGrouped[~dsGrouped['initialProjectionName'].isin(avoid)]
        m = max(m2 for (_, m2) in include) * 1.025
        include = [x for (x, _) in include]
        dsGrouped = dsGrouped[dsGrouped['initialProjectionName'].isin(include)]
        scale = alt.Scale(domain=(0, m))
        plotEnergy = alt.Chart().mark_point().encode(
          x=alt.X('innerEnergyWeighted0:Q', axis=axis, title='initially' + factorEnergyStr if showAxisLabel else None).scale(scale),
          y=alt.Y('innerEnergyWeightedThreshold:Q', axis=axis, title='optimized' + factorEnergyStr).scale(scale),
          color=alt.Color('case:N').scale(domain=domainLand, range=rangeLand),
          shape=alt.Shape('case:N', legend=alt.Legend(labelExpr=labelExprCase)).scale(domain=domainCase, range=rangeCase),
        ).properties(
          width=widthHeightChart,
          height=widthHeightChart,
        )
        return (plotDiagonal + plotEnergy).facet(
          facet=alt.Facet('initialProjectionName:N', title=None, header=alt.Header(labelOrient='top', labelPadding=-18, labelFontSize=11, labelFontWeight='bolder'), sort=include if include else None),
          columns=5,
          spacing=1,
          data=dsGrouped,
        )
      # chart b01
      configPlot(createPlot(createDictProjectionsM(), avoid=['unprojected'])).save(join(pathB, 'chart-b01.pdf'))
      # chart b01b
      dictProjectionsM = createDictProjectionsM()
      dictProjectionsMChunks = [dictProjectionsM[i : i + 5] for i in range(0, len(dictProjectionsM), 5)]
      plotsFacetted = alt.vconcat(*[createPlot(xs, showAxisLabel=i == len(dictProjectionsMChunks) - 1) for i, xs in enumerate(dictProjectionsMChunks)], spacing=4)
      configPlot(plotsFacetted, deltaLegendY=39).save(join(pathB, 'chart-b01b.pdf'))
      # ## CHART B/01/legend
      # base = alt.Chart(data).mark_line().encode(
      #   x=alt.value(0),
      #   y=alt.value(0),
      #   color=alt.Shape('case:N').scale(domain=domainLand, range=rangeLand),
      #   shape=alt.Shape('case:N', legend=alt.Legend(labelExpr=labelExprCase)).scale(domain=domainCase, range=rangeCase),
      # ).configure(
      #   **config,
      # ).configure_axis(
      #   **configAxis,
      # ).configure_view(
      #   **configView,
      # ).configure_view(
      #   stroke=None,
      # ).configure_legend(
      #   title=None,
      # ).transform_filter(
      #   alt.datum.step == 0
      # ).properties(
      #   width=1,
      #   height=1,
      # ).save(join(pathB, 'chart-b01-legend.pdf'))
      ## CHART B/02
      data = data[data['initialProjectionName'] != 'unprojected']
      dataLand = data[data['case'].str.contains('-land')].copy()
      dataNoLand = data[~data['case'].str.contains('-land')].copy()
      loop = [
        (None, dataNoLand, domainCaseNoLand, True),
        ('land', dataLand, domainCaseLand, False),
      ]
      def createPlot(label, data2, domainCase2, showLegend):
        return alt.Chart(data2).mark_point(clip=True).encode(
          x=alt.X('initialProjectionName:N', title=None), # 'projection'),
          xOffset=alt.Y('case:N'),
          y=alt.Y('innerEnergyWeighted:Q', title='inner energy' + (', ' + label if label else '') + factorEnergyStr).scale(alt.Scale(domain=(0, 19))),
          color=alt.Color('steps:N', legend=alt.Legend(labelExpr='datum.label == \'0\' ? \'0 steps\' : datum.label == \'100\' ? \'100 steps\' : datum.label') if showLegend else None).scale(scheme='category10'),
          shape=alt.Shape('case:N', legend=alt.Legend(labelExpr=labelExprCase, values=['default', 'distance-1.7', 'area-1.7']) if showLegend else None).scale(domain=domainCase2, range=rangeCaseLandNoLand),
        ).properties(
          width=620,
          # width=900,
          height=280,
        )
      alt.vconcat(*[createPlot(*x) for x in loop]).configure(
        **config,
      ).configure_axis(
        **configAxisWithGrid,
      ).configure_view(
        **configView,
      ).configure_legend(
        title=None,
        orient='top-right',
        offset=1,
        padding=5,
        fillColor='white',
      ).save(join(pathB, 'chart-b02.pdf'))
