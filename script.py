#!/usr/bin/env python3

import altair as alt
import csv
import os
import pandas as pd

from src.interfaces.script import DOMP, POTENTIAL, PROJECTION, Print

TESTING = False

ACTION_A = True
ACTION_B = True
CREATE_VISUALIZATION = True

pathA = 'A-optimization'
pathB = 'B-comparison-of-projections'
join = lambda *paths: os.path.expanduser(os.path.join('~', 'Downloads', *paths))

if ACTION_A or ACTION_B:
  with DOMP(cleanup=False) as domp:
    ### SETTINGS
    domp.resolution(3)
    domp.speed(4)
    domp.stopThreshold(maxForceStrength=.1 if not TESTING else .4, countDeficiencies=100, maxSteps=5000 if not TESTING else 500)
    domp.limitLatForEnergy(90)

    ### VIEW SETTINGS
    domp.viewForces(all=False)
    domp.viewEnergy(all=False)
    domp.viewNeighbours(show=False)
    domp.viewLabels(show=False)
    domp.viewSupportingPoints(active=False, weightsForPotential=None)
    domp.viewOriginalPolygons(show=False)
    domp.viewContinents(show=False)

    def defaultWeights():
      domp.weights(POTENTIAL.AREA, active=True, weightLand=1, weightOceanActive=True, weightOcean=.3, distanceTransitionStart=100, distanceTransitionEnd=800)
      domp.weights(POTENTIAL.DISTANCE, active=True, weightLand=1, weightOceanActive=True, weightOcean=.3, distanceTransitionStart=100, distanceTransitionEnd=800)
      domp.weights(POTENTIAL.DISTANCE_HOMOGENEITY, active=False, weightLand=.2, weightOceanActive=True, weightOcean=.05, distanceTransitionStart=100, distanceTransitionEnd=800)
      domp.weights(POTENTIAL.SHAPE, active=False, weightLand=.7, weightOceanActive=True, weightOcean=.3, distanceTransitionStart=100, distanceTransitionEnd=800)
      domp.weights(POTENTIAL.ORIENTATION, active=False, weightLand=.1, weightOceanActive=False, weightOcean=.1, distanceTransitionStart=100, distanceTransitionEnd=800)
      domp.weights(POTENTIAL.TRIANGLE_ALTITUDE, active=True, weightLand=1, weightOceanActive=False, weightOcean=.3, distanceTransitionStart=100, distanceTransitionEnd=800)

    ### A: OPTIMIZATION
    if ACTION_A:
      defaultWeights()
      for projection in PROJECTION.canBeOptimizedProjections:
        data = domp.startData(preventSnapshots=True)
        for i, context in enumerate(['supporting-points-forces-all', 'supporting-points-forces-all-individual', 'neighbours-continents']):
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
          if context == 'neighbours-continents':
            parts = ['neighbours', 'continents']
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
      domp.collectData(pathA + '/*/**/domp-optimization-*.csv', addPath=pathA, filename='domp-optimization.csv')

    ### B: COMPARISON OF PROJECTIONS
    if ACTION_B:
      def screenshot(projection, *parts):
        domp.screenshot(addPaths=[pathB, projection.name], addParts=parts)
      
      def dump(data, projection, parts, initial=False):
        potentials = [POTENTIAL.DISTANCE, POTENTIAL.AREA, POTENTIAL.TRIANGLE_ALTITUDE]
        # data
        domp.appendData(data, additionalData={'case': '-'.join(parts)})
        # original polygons
        if initial:
          domp.viewOriginalPolygons(show=True)
          screenshot(projection, 'original-polygons', *parts)
          domp.viewOriginalPolygons(show=False)
        # supporting points
        domp.viewSupportingPoints(active=True)
        screenshot(projection, 'supporting-points', *parts)
        # supporting points with labels
        domp.viewLabels(show=True)
        screenshot(projection, 'supporting-points-with-labels', *parts)
        domp.viewLabels(show=False)
        domp.viewSupportingPoints(active=False)
        # neighbours
        domp.viewNeighbours(show=True)
        screenshot(projection, 'neighbours', *parts)
        domp.viewNeighbours(show=False)
        # forces
        domp.viewForces(all=True, sum=True)
        screenshot(projection, 'forces', 'all', *parts)
        domp.viewForces(all=True, sum=False)
        screenshot(projection, 'forces', 'all', 'individual', *parts)
        for potential in potentials:
          domp.viewForces(potential=potential, sum=True)
          screenshot(projection, 'forces', potential.lower(), *parts)
          domp.viewForces(potential=potential, sum=False)
          screenshot(projection, 'forces', potential.lower(), 'individual', *parts)
        domp.viewForces(all=False, potential=None)
        # energies
        domp.viewEnergy(all=True)
        screenshot(projection, 'energies', 'all', *parts)
        for potential in potentials:
          domp.viewEnergy(potential=potential)
          screenshot(projection, 'energies', potential.lower(), *parts)
        domp.viewEnergy(all=False, potential=None)
        # continents
        domp.viewContinents(show=True)
        screenshot(projection, 'continents', *parts)
        domp.viewContinents(show=False)

      def runComparison(part):
        for projection in PROJECTION.allProjections:
          domp.limitLatForEnergy(90 if projection != PROJECTION.Mercator else 85.06)
          data = domp.startData(preventSnapshots=True)
          for considerContinents in [False, True]:
            # weights
            domp.weights(POTENTIAL.AREA, weightOceanActive=considerContinents)
            domp.weights(POTENTIAL.DISTANCE, weightOceanActive=considerContinents)
            # run
            parts = [part] + (['continents'] if considerContinents else [])
            domp.loadProjection(projection)
            dump(data, projection, parts, initial=True)
            if projection.canBeOptimized:
              domp.steps(100)
              dump(data, projection, parts)
              domp.steps()
              dump(data, projection, parts)
            # reset weights
            domp.weights(POTENTIAL.AREA, weightOceanActive=True)
            domp.weights(POTENTIAL.DISTANCE, weightOceanActive=True)
          domp.saveData(data, addPaths=[pathB, projection.name], filename='domp-comparison-of-projections-' + part + '.csv')

      defaultWeights()
      runComparison('default')

      defaultWeights()
      domp.weights(POTENTIAL.DISTANCE, active=True, weightLand=.3, weightOceanActive=False)
      runComparison('distance-0.3')

      defaultWeights()
      domp.weights(POTENTIAL.AREA, active=True, weightLand=.3, weightOceanActive=False)
      runComparison('area-0.3')

      domp.collectData(pathB + '/*/**/domp-comparison-of-projections-*.csv', addPath=pathB, filename='domp-comparison-of-projections.csv')

### CREATE VISUALIZATIONS
if CREATE_VISUALIZATION:
  factorEnergy = 1e8
  factorEnergyStr = ' [10^8]'
  factorEnergyTransform = {'energyWeighted': 'datum.energyWeighted / ' + str(factorEnergy)}
  stepsMax = 220
  ### A: OPTIMIZATION
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
    axis = alt.Axis(grid=False)
    base = alt.Chart(data).encode(
      color=alt.Color('initialProjectionName:N', legend=None).scale(scheme='category10'),
    )
    chartLine = base.mark_line(clip=True).encode(
      x=alt.X('step:Q', title='step').scale(domain=(0, 3 * stepsMax)),
      y=alt.Y('innerEnergyWeighted:Q', axis=axis, title='inner energy' + factorEnergyStr).scale(domain=(0, 1e9 / factorEnergy)),
      opacity=alt.value(.5),
    )
    chartLabel = base.mark_text(align='left', dx=5).encode(
      x=alt.X('step:Q', aggregate='max').scale(domain=(0, 3 * stepsMax)),
      y=alt.Y('innerEnergyWeighted:Q', aggregate='min'),
      text=alt.Text('initialProjectionName'),
    )
    (chartLine + chartLabel).configure_axis(
      grid=False,
    ).transform_filter(
      alt.datum.step < 3 * stepsMax
    ).properties(
      width=600,
      height=180,
    ).save(join(pathA, 'chart-a01.pdf'))
    ## CHART A/02
    data2Projections = ['Mercator', 'Gall-Peters', 'Natural Earth', 'Aitoff']
    data2 = data.copy()
    data2 = data2[data2['initialProjectionName'].isin(data2Projections)]
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
    base = alt.Chart(data2).encode(
      x=alt.X('step:Q', axis=alt.Axis(labels=False, title=None)).scale(scaleX),
      color=alt.Color('initialProjectionName:N', legend=alt.Legend(
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
    for proj in data2Projections:
      chartAlmostDeficienciesMaxs.append(baseDeficiencies.encode(
        x=alt.X('step:Q', axis=None).scale(scaleX),
        y=alt.Y('max_countAlmostDeficiencies:Q', axis=alt.Axis(minExtent=minExtent), title='almost def.').scale(domain=(0, 40)),
      ).transform_filter(
        (alt.datum.keep_countAlmostDeficiencies) & (alt.datum.initialProjectionName == proj)
      ).properties(**propertiesAlmostDeficiencies))
    chartAlmostDeficienciesArea = baseDeficienciesArea.encode(
      x=alt.X('step:Q', axis=None).scale(scaleX),
      y=alt.Y('min_countAlmostDeficiencies:Q', axis=alt.Axis(minExtent=minExtent), title='almost def.').scale(domain=(0, 40)),
      y2='max_countAlmostDeficiencies:Q',
    ).transform_filter(
      alt.datum.keep_countAlmostDeficiencies
    ).properties(**propertiesAlmostDeficiencies)
    chartDeficienciesMaxs = []
    for proj in data2Projections:
      chartDeficienciesMaxs.append(baseDeficiencies.encode(
        x=alt.X('step:Q', axis=None).scale(scaleX),
        y=alt.Y('max_countDeficiencies:Q', axis=alt.Axis(minExtent=minExtent), title='full def.').scale(domain=(0, 20), reverse=True),
      ).transform_filter(
        (alt.datum.keep_countDeficiencies) & (alt.datum.initialProjectionName == proj)
      ).properties(**propertiesDeficiencies))
    chartDeficienciesArea = baseDeficienciesArea.encode(
      x=alt.X('step:Q', axis=None).scale(scaleX),
      y=alt.Y('min_countDeficiencies:Q', axis=alt.Axis(minExtent=minExtent), title='full def.').scale(domain=(0, 20), reverse=True),
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
    ).configure_axis(
      grid=False,
    ).configure_legend(
      title=None,
      orient='top-right',
      offset=5,
    ).save(join(pathA, 'chart-a02.pdf'))
    ## CHART A/03
    scaleX = alt.Scale(domain=(0, stepsMax))
    minExtent = 25
    energiesOuterSubset = {
      'overall energy': 'outerEnergyWeighted',
      'distance energy': 'outerEnergyWeighted_DISTANCE',
      'area energy': 'outerEnergyWeighted_AREA',
    }
    base = alt.Chart(data2).encode(
      color=alt.Color('initialProjectionName:N').scale(scheme='category10'),
    )
    chartEnergies = []
    for i, (energyName, energy) in enumerate(energiesOuterSubset.items()):
      chartEnergies.append(base.mark_line(clip=True).encode(
        x=alt.X('step:Q', axis=alt.Axis(labels=(i == len(energiesOuterSubset) - 1), title=None)).scale(scaleX),
        y=alt.Y(energy + ':Q', axis=alt.Axis(minExtent=minExtent), title=energyName + factorEnergyStr).scale(domain=(0, 1e9 / factorEnergy)),
      ).properties(
        width=280,
        height=415/3,
      ))
    alt.vconcat(
      *chartEnergies,
      bounds='flush',
      spacing=10,
    ).configure_axis(
      grid=False,
    ).configure_legend(
      title=None,
      orient='top-right',
      offset=5,
    ).save(join(pathA, 'chart-a03.pdf'))
  ### B: COMPARISON OF PROJECTIONS
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
      data = data[data['initialProjectionName'] != 'unprojected']
      data = data[~data['initialProjectionName'].str.endswith(' (PROJ)')]
      data['steps'] = data['step'].apply(lambda step: int(step) if step in ['0', '100'] else 'threshold')
      data = data.sort_values(by=['case', 'initialProjectionName'])
    ## CHART B/01
    dataTmp = data.copy()
    dataTmp['innerEnergyWeighted0'] = data.apply(lambda row: row['innerEnergyWeighted'] if row['steps'] == 0 else None, axis=1).apply(pd.to_numeric)
    dataTmp['innerEnergyWeightedThreshold'] = data.apply(lambda row: row['innerEnergyWeighted'] if row['steps'] == 'threshold' else None, axis=1).apply(pd.to_numeric)
    dataGrouped = dataTmp.groupby(['initialProjectionName', 'case']).aggregate({'innerEnergyWeighted0': 'first', 'innerEnergyWeightedThreshold': 'first'})
    dataGrouped = pd.DataFrame(dataGrouped.to_records())
    m = max(*[dataGrouped[axisName].dropna().max() for axisName in ['innerEnergyWeighted0', 'innerEnergyWeightedThreshold']])
    scale = alt.Scale(domain=(0, m))
    axis = alt.Axis(grid=False)
    plotEnergy = alt.Chart().mark_point().encode(
      x=alt.X('innerEnergyWeighted0:Q', axis=axis, title='initially' + factorEnergyStr).scale(scale),
      y=alt.Y('innerEnergyWeightedThreshold:Q', axis=axis, title='optimized' + factorEnergyStr).scale(scale),
      color=alt.Color('case:N', legend=alt.Legend(
        labelExpr='datum.label == \'default\' ? \'default\' : datum.label == \'default-continents\' ? \'default (continents)\' : datum.label == \'distance-0.3\' ? \'distance\' : datum.label == \'distance-0.3-continents\' ? \'distance (continents\' : datum.label == \'area-0.3\' ? \'area\' : datum.label == \'area-0.3-continents\' ? \'area (continents)\' : \'-\'',
      )).scale(domain=['default', 'default-continents', 'distance-0.3', 'distance-0.3-continents', 'area-0.3', 'area-0.3-continents'], range=['#1f77b4', '#1f77b4', '#ff7f0e', '#ff7f0e', '#2ca02c', '#2ca02c']),
      shape=alt.Shape('case:N').scale(domain=['default', 'default-continents', 'distance-0.3', 'distance-0.3-continents', 'area-0.3', 'area-0.3-continents'], range=3 * ['circle', 'triangle']),
    ).properties(
      width=180,
      height=180,
    )
    plotDiagonal = alt.Chart().mark_rule(color='gray').encode(
      x=alt.value(0),
      x2=alt.value('width'),
      y=alt.value('height'),
      y2=alt.value(0),
      opacity=alt.value(.1),
    )
    (plotDiagonal + plotEnergy).facet(
      facet=alt.Facet('initialProjectionName:N', title=None, header=alt.Header(labelOrient='top', labelPadding=-20, labelFontSize=11, labelFontWeight='bolder')),
      columns=4,
      spacing=10,
      data=dataGrouped,
    ).configure_legend(
      title=None,
      orient='none',
      legendX=630,
      legendY=626,
    ).save(join(pathB, 'chart-b01.pdf'))
    ## CHART B/02
    alt.Chart(data).mark_point().encode(
      x=alt.X('initialProjectionName:N', title='projection'),
      xOffset=alt.Y('case:N'),
      y=alt.Y('innerEnergyWeighted:Q', title='inner energy' + factorEnergyStr),
      color=alt.Color('steps:N', legend=alt.Legend(labelExpr='datum.label == \'0\' ? \'0 steps\' : datum.label == \'100\' ? \'100 steps\' : datum.label')),
    ).configure_legend(
      title=None,
      orient='top-right',
      offset=1,
      padding=5,
      fillColor='white',
    ).properties(
      width=900,
      height=280,
    ).save(join(pathB, 'chart-b02.pdf'))
