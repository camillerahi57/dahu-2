import h5py
import pandas as pd
import plotly.graph_objs as go
import numpy as np
from pathlib import Path

from plotly.graph_objs import Figure

COLORSCALE = "plasma"
FONT = "DejaVu Sans"
FONT_COLOR = "#132440"


def get_hdf5_datasets(hdf5_file:h5py.Group, dataset_type:str):
    if dataset_type == "all":
        return list(hdf5_file.keys())

    else:
        dataset_list = []
        for dataset, dataset_group in hdf5_file.items():
            if "HT_type" in dataset_group.attrs:
                if dataset_type in dataset_group.attrs["HT_type"]:
                    dataset_list.append(dataset)

        return dataset_list


def colorbar_layout(z_min:float, z_max:float, precision:int=0, title:str=""):
    """
    Generates a standardized colorbar.

    Parameters:
        z_min : minimum value on the colorbar
        z_max : maximum value on the colorbar
        precision: number of digits on the colorbar scale
        title (str): The title of the plot.

    Returns:
        colorbar (dict): dictionary of colorbar parameters that can be
        passed to a figure.
    """
    z_mid = (z_min + z_max) / 2
    colorbar = dict(
        title=dict(
            text=f"{title} <br>&nbsp;<br>",
            font=dict(
                family=FONT,
                size=20,
                color=FONT_COLOR
            ),
        ),
        tickfont=dict(
            family=FONT,
            size=20,
            color=FONT_COLOR
        ),
        tickvals=[
            z_min,
            (z_min + z_mid) / 2,
            z_mid,
            (z_max + z_mid) / 2,
            z_max,
        ],  # Tick values
        ticktext=[
            f"{z_min:.{precision}f}",
            f"{(z_min + z_mid) / 2:.{precision}f}",
            f"{z_mid:.{precision}f}",
            f"{(z_max + z_mid) / 2:.{precision}f}",
            f"{z_max:.{precision}f}",
        ],  # Tick text
    )
    return colorbar


def heatmap_layout(title: str, size: int):
    """
    Generates a standardized layout for all heatmaps.

    Parameters:
        title (str): The title of the plot.

    Returns:
        go.Layout(): layout object that can be passed to a figure
        :param size: square size of the plot.
    """
    layout = go.Layout(
        title=dict(
            text=title,
            font=dict(
                family=FONT,
                size=24,
                color=FONT_COLOR
            )
        ),
        xaxis=dict(
            title="X (mm)",
            tickfont=dict(
                family=FONT,
                size=20,
                color=FONT_COLOR
            ),
            title_font=dict(
                family=FONT,
                size=20,
                color=FONT_COLOR
            ),
            range=[-43, 43],
            tickmode="linear",
            tick0=-40,
            dtick=10,
        ),
        yaxis=dict(
            title="Y (mm)",
            tickfont=dict(
                family=FONT,
                size=20,
                color=FONT_COLOR
            ),
            title_font=dict(
                family=FONT,
                size=20,
                color=FONT_COLOR
            ),
            range=[-43, 43],
            tickmode="linear",
            tick0=-40,
            dtick=10,
        ),
        width=size,
        height=size - 40,
        margin=dict(r=100, t=100),
    )
    return layout


def edx_make_results_dataframe_from_hdf5(edx_group:h5py.Group):
    data_dict_list = []
    positions_group = edx_group["positions"]
    for position, position_group in positions_group.items():
        instrument_group = position_group.get('instrument')

        results_group = position_group.get('results')

        data_dict = {"x_pos (mm)": instrument_group["x_pos"][()],
                     "y_pos (mm)": instrument_group["y_pos"][()],
                     "ignored": position_group.attrs["ignored"]}

        if results_group is not None:
            for element, element_group in results_group.items():
                if 'AtomPercent' in element_group:
                    atom_percent = element_group['AtomPercent'][()]
                    data_dict[f"{element}_(at.%)"] = atom_percent

        data_dict_list.append(data_dict)

    result_dataframe = pd.DataFrame(data_dict_list)

    return result_dataframe


def moke_make_results_dataframe_from_hdf5(moke_group:h5py.Group):
    data_dict_list = []
    positions_group = moke_group["positions"]
    for position, position_group in positions_group.items():

        if "scan_parameters" in position:
            continue

        instrument_group = position_group.get("instrument")

        results_group = position_group.get("results")

        data_dict = {
            "x_pos (mm)": instrument_group["x_pos"][()],
            "y_pos (mm)": instrument_group["y_pos"][()],
            "ignored": position_group.attrs["ignored"],
        }

        if results_group is not None:
            for value, value_group in results_group.items():
                if value == "parameters":
                    continue
                if isinstance(value_group, h5py.Group):
                    value_group = value_group["mean"]

                if "units" in value_group.attrs:
                    units = value_group.attrs["units"]
                else:
                    units = "arb"

                data_dict[f"{value}_({units})"] = value_group[()]

        data_dict_list.append(data_dict)

    result_dataframe = pd.DataFrame(data_dict_list)

    return result_dataframe


def profil_make_results_dataframe_from_hdf5(profil_group):
    valid_results = ["measured_thickness", "sample_thickness"]
    data_dict_list = []
    positions_group = profil_group["positions"]

    for position, position_group in positions_group.items():
        instrument_group = position_group.get("instrument")

        results_group = position_group.get("results")

        data_dict = {"x_pos (mm)": instrument_group["x_pos"][()],
                     "y_pos (mm)": instrument_group["y_pos"][()],
                     "ignored": position_group.attrs["ignored"]}

        if results_group is not None:
            for value, value_group in results_group.items():
                if value in valid_results:
                    if "units" in value_group.attrs:
                        units = value_group.attrs["units"]
                    else:
                        units = "arb"
                    data_dict[f"{value}_({units})"] = value_group[()]

            data_dict_list.append(data_dict)

    result_dataframe = pd.DataFrame(data_dict_list)

    return result_dataframe


def make_heatmap_from_dataframe(
    df:pd.DataFrame,
    values:str="",
    precision:int=0,
    plot_title:str="",
    colorbar_title:str="",
    masking:bool=False,
    colorscale:str=COLORSCALE,
    *,
    size: int,
) -> Figure:

    if values not in df.columns:
        raise KeyError(f"{values} is not a valid dataframe column. "
                       f"Valid entries are: {df.columns}")

    heatmap_data = df.pivot_table(
        index="y_pos (mm)",
        columns="x_pos (mm)",
        values=values,
    )

    # If mask is set, hide points that have an ignore tag in the database
    if masking:
        # Create a mask to hide ignored points
        mask_data = df.pivot_table(
            index="y_pos (mm)", columns="x_pos (mm)", values="ignored"
        )
        # Ignore points
        mask = mask_data == False

        heatmap_data = heatmap_data.where(mask, np.nan)

    z_min = np.nanmin(heatmap_data.values)
    z_max = np.nanmax(heatmap_data.values)

    heatmap = go.Heatmap(
        x=heatmap_data.columns,
        y=heatmap_data.index,
        z=heatmap_data.values,
        colorscale=colorscale,
        # Set ticks for the colorbar
        colorbar=colorbar_layout(z_min, z_max, precision, title=colorbar_title),
    )

    # Make and show figure
    fig = go.Figure(data=[heatmap],
                    layout=heatmap_layout(title=f"{plot_title} <br> {values}",
                                          size=size),
                    )

    if z_min is not None:
        fig.data[0].update(zmin=z_min)
    if z_max is not None:
        fig.data[0].update(zmax=z_max)

    return fig



def make_heatmaps_from_hdf5(hdf5_path:str | Path, data_type:str, size: int):
    allowed_types = ["edx", "profil", "moke"]
    if data_type not in allowed_types:
        raise ValueError("Unsupported data_type passed to "
                         "make_heatmaps_from_hdf5")

    fig_list: list[Figure] = []

    with h5py.File(hdf5_path, "r") as hdf5_file:
        hdf5_groups = get_hdf5_datasets(hdf5_file, data_type)
        if len(hdf5_groups) > 1:
            raise ValueError(f"Multiple datasets of type {data_type} "
                             f"found in {hdf5_path}")

        hdf5_group = hdf5_file[hdf5_groups[0]]

        if data_type == "edx":
            results_df = edx_make_results_dataframe_from_hdf5(hdf5_group)
            precision = 0
            title = "EDX Composition"
        elif data_type == "profil":
            results_df = profil_make_results_dataframe_from_hdf5(hdf5_group)
            precision = 0
            title = "Profilometry Thickness"
        elif data_type == "moke":
            results_df = moke_make_results_dataframe_from_hdf5(hdf5_group)
            title = "MOKE Magnetic Properties"
            precision = 3
        else:
            raise ValueError(f"Unsupported data_type passed to "
                             f"make_heatmaps_from_hdf5. Also, how did you "
                             f"get here???")

    print(results_df)

    for key in results_df.columns:
        if key in ["x_pos (mm)", "y_pos (mm)", "ignored"]:
            continue

        unit = key.split("_")[-1]
        fig = make_heatmap_from_dataframe(results_df,
                                          key,
                                          precision=precision,
                                          plot_title=title,
                                          colorbar_title=unit,
                                          masking=True,
                                          size=size,
                                          )
        fig_list.append(fig)

    return fig_list

