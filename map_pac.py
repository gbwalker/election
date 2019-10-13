def map_pac():
    
    # Select a PAC at random.
        
    pac = df_individuals.drop_duplicates(subset='recipient').recipient.sample(1).iloc[0]
    
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
        zoom_start=5,
        min_zoom=4,
        prefer_canvas=True
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

    # Add a red dot for transactions sent by the PAC, not received.
    # Identify transactions of interest based on recipient zip codes.
    
    df_transfers = df_cc[df_cc.sender == pac][['city', 'state', 'zip', 'amount', 'date', 'recipient', 'image']]
    
    # If there are transactions, proceed.
    
    if not df_transfers.empty:

        # Make another layer for transactions, not donations.
        
        transfer_layer = folium.FeatureGroup(name='Transfers').add_to(m)

        # Find zips where funds were transfered to.
        
        pac_zip_transfers = zip_points[zip_points.zip.astype('int').isin(list(df_transfers.zip.values.astype('int')))]

        # Add the center point to the information about the received transaction.
        
        df_transfers = pd.merge(df_transfers, pac_zip_transfers[['zip', 'center']], how='left', on='zip').dropna(axis='rows')
        
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

    return