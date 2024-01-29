class InterfaceCommon:
  @staticmethod
  def isStopThresholdReached(geoGrid, geoGridSettings):
    # maxForceStrength is in units of the coordinate system in which the cells are located: radiusEarth * deg2rad(lon), radiusEarth * deg2rad(lat)
    # maxForceStrength is divided by the typical distance (which works perfectly at the equator) to normalize
    # The normalized maxForceStrength is divided by the speed (100 * (1 - dampingFactor)), in order to compensate for varying speeds
    stopThresholdReached = geoGrid.maxForceStrength() / (100 * (1 - geoGridSettings._dampingFactor)) < geoGridSettings._stopThreshold * geoGridSettings._typicalDistance
    if stopThresholdReached:
      geoGridSettings.setThresholdReached()
    return stopThresholdReached
