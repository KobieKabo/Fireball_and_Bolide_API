@app.route('/graph/<graph_data>', methods = ['GET','POST','DELETE'])
def create_graph(graph_data:str):
    """
    """
    
    if request.method == 'DELETE':
        rd_image.flushdb()
        return 'The graphs have been removed from the redis database.\n'

    elif request.method == 'POST':
        if (len(rd.keys()) == 0):
            return 'No data is available. Please Post the data.'
        else:
            if graph_data == 'energy':
                energy_radiated = []
                ttl_impact_energy = []
                keys = rd.keys()
                for key in keys:
                    if rd.hget(key, 'radiated_energy') is not None and rd.hget(key, 'impact_energy') is not None:
                        # Need to ensure array sizes are the same.
                        energy_radiated.append(float(rd.hget(key, 'radiated_energy')))
                        ttl_impact_energy.append(float(rd.hget(key, 'impact_energy')))

                fig1 = plt.figure()
                plt.scatter(energy_radiated, ttl_impact_energy)
                plt.title('Energy Radiated vs Meteor Impact Energy')
                plt.xlabel('Total Energy Radiated')
                plt.ylabel('Total Impact Energy')

                buf = io.BytesIO()
                plt.savefig(buf, format = 'jpg')
                buf.seek(0)

                image_data = buf.getvalue()

                rd_image.set('image', image_data.hex())

                return 'Image has been posted.\n'

            elif graph_data == 'location':
                latitude_pos = []
                longitude_pos = []
                keys = rd.keys()
                for key in keys:
                    if rd.hget(key, 'latitude') is not None and rd.hget(key,'longitude') is not None:
                        latitude_pos.append(rd.hget(key,'latitude'))
                        longitude_pos.append(rd.hget(key,'longitude'))
                 
                lat_deg = [sub[:-1] for sub in latitude_pos]
                latitude_dir = [sub[-1] for sub in latitude_pos]

                lat_dir = []
                for x in latitude_dir:
                    if 'S' in x:
                        lat_dir.append(-1)
                    else:
                        lat_dir.append(1)

                long_deg = [sub[:-1] for sub in longitude_pos]
                longitude_dir = [sub[-1] for sub in longitude_pos]
                long_dir = []
                for x in longitude_dir:
                    if 'W' in x:
                        long_dir.append(-1)
                    else:
                        long_dir.append(1)

                latitude_pos = []
                longitude_pos = []

                for x in range(0,len(lat_dir)):
                    latitude_pos.append(lat_dir[x] * lat_deg[x])
                for x in range(0,len(long_dir)):
                    longitude_pos.append(long_dir[x] * long_deg[x])
                

                fig2 = plt.figure(figsize=(8,6), edgecolor ='w')
                m = Basemap(projection = 'cyl', resolution = None,\
                            llcrnrlat=-90, urcrnrlat=90,\
                            llcrnrlon=-180, urcrnrlon=180,)
                draw_map(m)

                plt.scatter(longitude_pos, latitude_pos)

                buf = io.BytesIO()
                plt.savefig(buf, format = 'jpg')
                buf.seek(1)

                image_data = buf.getvalue()

                rd_image.set('image2', image_data.hex())

                return 'Image has been posted.\n'


    # posting/getting are identical to my hw8, which was working. Should work once POST does.
    elif request.method == 'GET':
        if graph_data == 'energy':
            image = binascii.unhexlify(rd_image.get('image'))
            buf = io.BytesIO(image)
            buf.seek(0)

            response = send_file(buf, mimetype = 'image/jpg', as_attachment=True, download_name='energy_graph.jpg')

            return response

        elif graph_data == 'location':
            image = binascii.unhexlify(rd_image.get('image2'))
            buf = io.BytesIO(image)
            buf.seek(1)
            response = send_file(buf, mimetype = 'image/jpg', as_attachment=True, download_name='geograph_graph.jpg')

            return response

    else:
        return 'The method used is not supported. Please use GET, DELETE, or POST.'

def draw_map(m, scale=0.2):
    # draw a shaded-relief image
    m.shadedrelief(scale=scale)
    
    # lats and longs are returned as a dictionary
    lats = m.drawparallels(np.linspace(-90, 90, 13))
    lons = m.drawmeridians(np.linspace(-180, 180, 13))

    # keys contain the plt.Line2D instances
    lat_lines = chain(*(tup[1][0] for tup in lats.items()))
    lon_lines = chain(*(tup[1][0] for tup in lons.items()))
    all_lines = chain(lat_lines, lon_lines)
    
    # cycle through these lines and set the desired style
    for line in all_lines:
        line.set(linestyle='-', alpha=0.3, color='w')

