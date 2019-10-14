# This function produces an HTML map for the app to display.

import numpy as np
import pandas as pd
import folium
import json

def map_pac(pac, df_individuals, zip_points, sf_states, state_abbreviations, df_cc):
    
    ###############
    # PAC DONATIONS
    ###############
    
    # Filter transactions for just the ones that the PAC sent.
    # Also delete any null values.
    
    df = df_individuals[df_individuals.recipient == pac][['first_last', 'city', 'state', 'zip', 'amount', 'date', 'image']].dropna(axis='rows')
     
    # Get the zip codes and states from which individuals have contributed OR where the PAC has sent funds.
    
    pac_zip_points = zip_points[zip_points.zip.astype('int').isin(list(df.zip.values.astype('int')))].dropna(axis='rows')[['zip', 'center']]
    
    states = df_individuals[df_individuals.recipient == pac].state.drop_duplicates().dropna(axis='rows')
    
    # Merge the full donation data with the zip code center points.
    
    if not pac_zip_points.zip.empty:
    
        df = pd.merge(df, pac_zip_points, how='left', on='zip')
        
        # Delete null donation amounts.
        
        df = df.dropna(axis='rows')
        
    # If no zip code points exist, use the centroids of each of the states.
    
    if pac_zip_points.zip.empty:
        
        pac_zip_points = sf_states[sf_states.name.isin(states)].assign(geometry=sf_states.geometry.centroid)
        
        pac_zip_points.columns = ['state', 'geometry']
        
        # Merge in the center points by state.
        
        df = pd.merge(df, pac_zip_points, how='left', on='state')
        
    # Sum donations by state for creating a choropleth.
    
    df_state_totals = df.groupby('state').sum().reset_index()[['state', 'amount']]
    
    # Also get state polygons for the relevant transactions.
    
    pac_states = sf_states[sf_states.name.isin(df.state)]
    
    # Map the state areas with a choropleth.
    
    json_states = pac_states.__geo_interface__

    # Create a state mapping for abbreviations.
    
    state_mapping = dict(zip(state_abbreviations.state, state_abbreviations.abbreviation))

    ### Create the map.

    m = folium.Map(
        location=[39.5, -98.35],
        tiles=None,
        zoom_start=4,
        min_zoom=4,
        prefer_canvas=True,
        zoom_control=False
        )
    
    folium.TileLayer(
        tiles='cartodbpositron',
        min_zoom=4,
        name='PAC donations by state'
    ).add_to(m)

    # Add a choropleth layer for the state.

    folium.Choropleth(
        geo_data=json_states,
        name='Donations',
        data=df_state_totals,
        columns=['state', 'amount'],
        key_on='feature.properties.name',
        fill_color='YlGn',
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name='State-wide donations ($)',
        control=False
    ).add_to(m)
    
    # Add transparent popup donation amounts for each state.
        
    donation_overlay = pd.merge(pac_states, df_state_totals, how='left', left_on='name', right_on='state')[['name', 'geometry', 'amount']]
    
    # Make sure the amounts display as formatted strings (dollar sign + comma) rather than just integers.
    
    donation_overlay = donation_overlay.assign(amount='$' + donation_overlay.apply(lambda x: "{:,}".format(x['amount']), axis=1))
    
    folium.GeoJson(
        data=donation_overlay.to_json(),
        name='State donations',
        show=True,
        control=False,
        style_function=lambda feature: {
            'color': 'black',
            'weight': 0.25,
            'fillOpacity': 0
        },   
        tooltip=folium.features.GeoJsonTooltip(
            fields=['name', 'amount'],
            aliases=['State:', 'Contributions:'],
            style=''
        )
    ).add_to(m)

    # Add points to the map representing where donations are from.
    # Start with a layer for contributions.
    
    contribution_layer = folium.FeatureGroup(name='Contributions').add_to(m)
    
    # Format the donation amounts with a dollar sign and comma.
    
    df = df.assign(amount='$' + df.apply(lambda x: "{:,}".format(x['amount']), axis=1))
    
    # Make a custom jitter function for the coordinates of the points.
    
    def jitter(n):
        
        return n * (1 + np.random.rand() * .001)
    
    for n in range(len(df)):
        
        # Assign the amount, name, etc. to display.
        # Get the state abbreviation with the state mapping.
        
        amount = df.amount.iloc[n]
        
        date = str(df.date.iloc[n])
        
        name = df.first_last.iloc[n]
        
        city = df.city.iloc[n]
        
        state = state_mapping[df.state.iloc[n]]
        
        zip_code = str(df.zip.iloc[n])
        
        link = '<a href=\"https://docquery.fec.gov/cgi-bin/fecimg/?' + str(df.image.iloc[n]) + '\" target=\"_blank\">Documentation</a>'
        
        # Create a popup with the link to the reference document.
        
        popup_link = folium.Popup(link)
                
        # Plot the points.
        
        folium.CircleMarker(
            location=(jitter(df.center.iloc[n].y), jitter(df.center.iloc[n].x)),
            tooltip=(amount + '<br/>' + date + '<br/>' + name + '<br/>' + city + ', ' + state + ' ' + zip_code),
            popup=popup_link,
            radius=4,
            color='white',
            fill=True,
            fill_color='green',
            fill_opacity=1
        ).add_to(contribution_layer)

    ##################
    # PAC TRANSACTIONS
    ##################

    # Add a red dot for transactions sent by the PAC, not received.
    # Identify transactions of interest based on recipient zip codes.
    
    df_transfers = df_cc[df_cc.sender == pac][['city', 'state', 'zip', 'amount', 'date', 'recipient', 'image']]
    
    # Drop all transfers with missing information.
    
    df_transfers = df_transfers.dropna(axis='rows')
    
    # If there are transactions, proceed.
    
    if not df_transfers.empty:

        # Make another layer for transactions, not donations.
        
        transfer_layer = folium.FeatureGroup(name='Transfers').add_to(m)

        # Find zips where funds were transfered to.
        
        pac_zip_transfers = zip_points[zip_points.zip.astype('int').isin(list(df_transfers.zip.values.astype('int')))]

        # Add the center point to the information about the received transaction.
        
        df_transfers = pd.merge(df_transfers, pac_zip_transfers[['zip', 'center']], how='left', on='zip')
        
        # If there are no zip codes found, use the point associated with another zip code in the same city.
        
        df_transfers_pointless = df_transfers[df_transfers.apply(lambda x: str(x['center']) == 'nan', axis='columns')]
        
        if not df_transfers_pointless.empty:
            
            # Save the replacement points into a list.
            
            new_points = []
        
            for n in range(len(df_transfers_pointless)):
                                
                # If the zip code isn't in the zip code points list, find a random zip with the same city and state. If there's no city and state, use the center of the state.
                
                replacement_points = zip_points[(zip_points.state ==      df_transfers_pointless.state.iloc[n]) & (zip_points.city == df_transfers_pointless.city.iloc[n])]
                
                if not replacement_points.empty:
                    
                    new_points.append(replacement_points.sample(1).center.iloc[0])
                
                if replacement_points.empty:
                    
                    new_points.append(sf_states[sf_states.name == df_transfers_pointless.state.iloc[n]].geometry.centroid)

            # Match the pointless index to the new points so they can be assigned correctly.
            
            new_points = pd.Series(new_points, index=df_transfers_pointless.index)

            # Assign the new points to the pointless values.
            
            df_transfers_pointless = df_transfers_pointless.assign(center=pd.Series(new_points))

            # Delete all blank values in the original list and merge back in replacements.
            
            df_transfers = pd.merge(df_transfers, df_transfers_pointless.center, how='outer', left_index=True, right_index=True)
            
            # Combine the two center columns.
            
            df_transfers = df_transfers.assign(center=df_transfers.center_x.fillna(df_transfers.center_y))
            
            del df_transfers['center_x']
            del df_transfers['center_y']
            
        # Format amounts with a $ and comma.
        
        df_transfers = df_transfers.assign(amount='$' + df_transfers.apply(lambda x: "{:,}".format(x['amount']), axis=1))
        
        # Drop any null values.
        
        df_transfers = df_transfers.dropna(axis='rows')

        # Plot all the sent transactions.
        
        for n in range(len(df_transfers)):
            
            # Assign the amount, name, etc. to display.
            # Get the state abbreviation with the state mapping.
            
            amount = df_transfers.amount.iloc[n]
            
            date = str(df_transfers.date.iloc[n])
            
            recipient = df_transfers.recipient.iloc[n]
            
            city = df_transfers.city.iloc[n]
            
            state = state_mapping[df_transfers.state.iloc[n]]
            
            zip_code = str(df_transfers.zip.iloc[n])
                    
            link = '<a href=\"https://docquery.fec.gov/cgi-bin/fecimg/?' + str(df_transfers.image.iloc[n]) + '\" target=\"_blank\">Documentation</a>'
            
            # Create a popup with the link to the reference document.
            
            popup_link = folium.Popup(link)
            
            # Then add the marker.
            
            folium.CircleMarker(
                location=(jitter(df_transfers.center.iloc[n].y), jitter(df_transfers.center.iloc[n].x)),
                tooltip=(recipient + '<br/>' + amount + '<br/>' + date + '<br/>' + city + ', ' + state + ' ' + zip_code),
                popup=popup_link,
                radius=4,
                color='red',
                fill=True,
                fill_color='red',
                fill_opacity=1
            ).add_to(transfer_layer)

    folium.LayerControl().add_to(m)

    # Save the map output.

    m.save('map.html')