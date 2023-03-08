"""Generate travel directions based on a travel mode."""

import arcpy


def get_directions():
    """Generate travel directions based on a travel mode."""
    # Read inputs
    stops = arcpy.GetParameter(0)
    # Performance tip: The network data source should be read using the arcpy.GetParameterAsText() method instead of the
    # arcpy.GetParameter() method since GetParameterAsText provides access to the network data source much faster
    network_data_source = arcpy.GetParameterAsText(1)
    travel_mode = arcpy.GetParameter(2)
    start_time = arcpy.GetParameter(3)
    output_directions = arcpy.GetParameterAsText(4)

    # Initialize Route solver and set analysis settings
    route_solver = arcpy.nax.Route(network_data_source)
    route_solver.travelMode = travel_mode
    route_solver.timeOfDay = start_time
    route_solver.returnDirections = True

    # Load inputs
    route_solver.load(arcpy.nax.RouteInputDataType.Stops, stops)

    # Solve. A network analyst license is required when solving
    arcpy.CheckOutExtension("network")
    result = route_solver.solve()

    # Print all the warning and error messages in case the solve is not successful
    if not result.solveSucceeded:
        arcpy.AddMessage("Solve failed")
        warning_msgs = result.solverMessages(arcpy.nax.MessageSeverity.Warning)
        error_msgs = result.solverMessages(arcpy.nax.MessageSeverity.Error)
        for msg in warning_msgs:
            arcpy.AddWarning(msg[-1])
        for msg in error_msgs:
            arcpy.AddError(msg[-1])
        raise SystemExit(1)

    # Export the directions
    result.export(arcpy.nax.RouteOutputDataType.Directions, output_directions)


if __name__ == "__main__":
    get_directions()
