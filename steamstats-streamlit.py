import urllib
import requests

import numpy as np
import pandas as pd
import altair as alt
import streamlit as st

import matplotlib.pyplot as plt

st.set_page_config(layout="wide")

st.title("CS:GO Steam Stats")

steamid = st.text_input("Steam ID", "76561198020908104")
# key = st.text_input("Steam API Key", "AA1A1F692E6D48BFC0F23FB2F7313A2B")

key = 'AA1A1F692E6D48BFC0F23FB2F7313A2B'

# # ----------- Temporary Placeholders ----------- #
# steamid = '76561198020908104'
# key = 'AA1A1F692E6D48BFC0F23FB2F7313A2B'
# # ---------------------------------------------- #

col1, col2, col3 = st.beta_columns([1, 1.5, 1.5])


def get_api_link(interface: str, method: str, version: str, **kwargs):
    url = f'https://api.steampowered.com/{interface}/{method}/v000{version}'
    if kwargs:
        url += '/?'
        for key in kwargs:
            url += str(key) + '=' + str(kwargs[key]) + '&'
    return url


def get_ordered_numbers(r: dict, search_term: str, ignore_terms: list = None, high_to_low: bool = True, truncate_name: bool = True):
    item_dict = {}

    for item in r['playerstats']['stats']:
        if search_term in item['name']:
            if ignore_terms:
                res = any(ele in item['name'] for ele in ignore_terms)
                if not res:
                    if truncate_name:
                        item_dict[item['name'].split('_')[-1]] = int(item['value'])
                    else:
                        item_dict[item['name']] = int(item['value'])
            else:
                if truncate_name:
                    item_dict[item['name'].split('_')[-1]] = int(item['value'])
                else:
                    item_dict[item['name']] = int(item['value'])

    items_ordered = {k: v for k, v in sorted(item_dict.items(), key=lambda item: item[1], reverse=high_to_low)}
    item_list = items_ordered.items()

    if bool(item_list):
        name, number = zip(*item_list)
    else:
        print(f'No items match search term: "{search_term}"')
        return None, None, None

    if len(name) == 1:
        name = name[0]

    if len(number) == 1:
        number = number[0]

    return name, number, items_ordered


if steamid and key:
    link = get_api_link('ISteamUserStats', 'GetUserStatsForGame', '2', key=key, steamid=steamid, appid='730')
    link_2 = get_api_link('ISteamUser', 'GetPlayerSummaries', '2', key=key, steamids=steamid, appid='730')
    r = requests.get(link).json()
    r_2 = requests.get(link_2).json()

    _, _, headshots = get_ordered_numbers(r, 'headshot')
    _, _, damage = get_ordered_numbers(r, 'damage', truncate_name=False)
    _, _, rounds = get_ordered_numbers(r, 'total_rounds_played', truncate_name=False)
    _, _, last_rounds = get_ordered_numbers(r, 'last_match_rounds', truncate_name=False)
    _, _, kills_ratio = get_ordered_numbers(r, 'kills', truncate_name=False)
    _, _, deaths_ratio = get_ordered_numbers(r, 'deaths', truncate_name=False)
    _, _, lm_t = get_ordered_numbers(r, 'last_match_t_wins', truncate_name=False)
    _, lm_k_val, lm_k = get_ordered_numbers(r, 'last_match_kills', truncate_name=False)
    _, lm_d_val, lm_d = get_ordered_numbers(r, 'last_match_deaths', truncate_name=False)

    tk_name, tk_val, tk_ordered = get_ordered_numbers(r, 'total_kills')
    headshot_name, headshot_val, headshot = get_ordered_numbers(r, 'headshot', truncate_name=False)
    _, mvp_val, mvps = get_ordered_numbers(r, 'total_mvps', truncate_name=False)
    tsf_name, tsf_val, _ = get_ordered_numbers(r, 'total_shots_fired', truncate_name=False)
    tsh_name, tsh_val, _ = get_ordered_numbers(r, 'total_shots_hit', truncate_name=False)

    acc = tsh_val * 100 / tsf_val

    hs_perc = headshot_val * 100 / tk_ordered['kills']

    KD_ratio = kills_ratio['total_kills'] / deaths_ratio['total_deaths']

    last_match_team_won = 'Terrorist' if lm_t else 'Counter Terrorist'
    last_match_kd = lm_k_val / lm_d_val

    adr = damage['total_damage_done'] / rounds['total_rounds_played']
    last_adr = damage['last_match_damage'] / last_rounds['last_match_rounds']

    img = urllib.request.urlopen(r_2['response']['players'][0]['avatarfull'])
    a = plt.imread(img, format='jpg')

    with col1:
        st.image(a)
        st.write(r_2['response']['players'][0]['realname'])

    with col2:
        st.write('Overall ADR:', f"{adr:.01f}")
        st.write('Last Match ADR:', f"{last_adr:.01f}")
        st.write('Overall KD Ratio:', f"{KD_ratio:.01f}")
        st.write('Last Match KD Ratio:', f"{last_match_kd:.01f}")

    with col3:
        st.write('Accuracy:', f"{acc:0.1f}%")
        st.write('Headshots:', f"{headshots['headshot']}")
        st.write('Headshot percentage:', f"{hs_perc:.01f}%")
        st.write('MVPs:', f"{mvp_val}")

    # ---------------------- Kills / Weapon Barchart ---------------------- #
    st.text("")
    st.text("")
    st.text("")

    ignore_terms = ['headshot', 'sniper', 'enemy_weapon', 'elite', 'fight', 'elite']
    _, _, total_kills_ordered = get_ordered_numbers(r, 'total_kills_', ignore_terms)

    limit = st.slider('Number of weapons to display',
                      min_value=1,
                      max_value=len(total_kills_ordered.keys()),
                      value=7)

    col3, col4 = st.beta_columns(2)

    with col3:
        kills_df = pd.DataFrame(list(total_kills_ordered.items())[:limit], columns=['weapon', 'kills'])

        bar_chart_kills = alt.Chart(kills_df, title='Kills').mark_bar(opacity=0.7).encode(
            alt.X('weapon', sort=alt.EncodingSortField(field="kills", op="count", order='ascending'),
                  axis=alt.Axis(grid=False, title=None)),
            alt.Y('kills', axis=alt.Axis(grid=True, title=None)),
            color=alt.Color('weapon', scale=alt.Scale(range=['#4c78a8']), legend=None)
        )

        text_0 = bar_chart_kills.mark_text(baseline='bottom', align='center').encode(text='kills')

        tmp_chart_0 = alt.layer(bar_chart_kills, text_0).configure_axis(labelFontSize=12, titleFontSize=16).configure_title(
            fontSize=20).configure_view(stroke='transparent')

        st.altair_chart(tmp_chart_0, use_container_width=True)
    # ------------------------------------------------------------ #

    # ---------------------- Shots vs Hits / Weapon Barchart ---------------------- #
    with col4:
        link = get_api_link('ISteamUserStats', 'GetUserStatsForGame', '2', key=key, steamid=steamid, appid='730')
        r = requests.get(link).json()

        ignore_terms = ['fired', '_hit', 'elite']
        _, _, total_shots_ordered = get_ordered_numbers(r, 'total_shots_', ignore_terms)
        _, _, total_hits_ordered = get_ordered_numbers(r, 'total_hits_')

        shots_df = pd.DataFrame(list(total_shots_ordered.items())[:limit], columns=['weapon', 'shots'])
        hits_df = pd.DataFrame(list(total_hits_ordered.items())[:limit], columns=['weapon', 'hits'])

        combined_df = pd.merge(shots_df, hits_df, on='weapon')

        test_data_melted = pd.melt(combined_df, id_vars='weapon',
                                   var_name="source", value_name="value_numbers")

        bar_chart_shots_2 = alt.Chart(test_data_melted, title='Shots vs Hits').mark_bar(opacity=0.7).encode(
            x=alt.X('weapon', sort=['value_numbers'], axis=alt.Axis(grid=False, title=None)),
            y=alt.Y('value_numbers', axis=alt.Axis(grid=True, title=None), stack=None),
            color=alt.Color('source', scale=alt.Scale(range=['#f63366', '#4c78a8']))
        )

        text_1 = bar_chart_shots_2.mark_text(baseline='bottom', align='center').encode(text='value_numbers')

        tmp_chart_1 = alt.layer(bar_chart_shots_2, text_1).configure_axis(
            labelFontSize=12, titleFontSize=16).configure_title(
            fontSize=20).configure_view(stroke='transparent').configure_legend(orient='right')

        st.altair_chart(tmp_chart_1, use_container_width=True)
    # ----------------------------------------------------------------------------- #

    weapons_list = sorted(list(total_shots_ordered.keys()))
    weapon = st.selectbox('Select your weapon', weapons_list)

    st.text("")
    st.text("")
    # st.text("")

    kills_df = pd.DataFrame(list(total_kills_ordered.items()), columns=['weapon', 'kills'])
    shots_df = pd.DataFrame(list(total_shots_ordered.items()), columns=['weapon', 'shots'])
    hits_df = pd.DataFrame(list(total_hits_ordered.items()), columns=['weapon', 'hits'])

    combined_df = pd.merge(shots_df, hits_df, on='weapon')

    combined_df_2 = pd.merge(combined_df, kills_df, on='weapon')
    test_data_melted_2 = pd.melt(combined_df_2, id_vars='weapon',
                                 var_name="source", value_name="value_numbers")

    weapon_df = test_data_melted_2[test_data_melted_2['weapon'] == weapon]

    bar_chart_weapon = alt.Chart(weapon_df, title=f'Stats for {weapon}').mark_bar(opacity=0.7).encode(
        x=alt.X('source', sort=['value_numbers'], axis=None, title=''),
        y=alt.Y('value_numbers:Q', title=''),
        color=alt.Color('source', scale=alt.Scale(range=['#31333f', '#f63366', '#4c78a8']))
    )

    text_2 = bar_chart_weapon.mark_text(baseline='bottom', align='center', size=15).encode(text='value_numbers')

    tmp_chart_2 = alt.layer(bar_chart_weapon, text_2).configure_axis(labelFontSize=12, titleFontSize=16).configure_title(
        fontSize=20).configure_view(stroke='transparent').configure_legend(orient='bottom')

    st.altair_chart(tmp_chart_2, use_container_width=True)
