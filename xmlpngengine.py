# import os
import xml.etree.ElementTree as ET
from PIL import Image

def pad_img(img, clip=False, top=2, right=2, bottom=2, left=2):
    if clip:
        img = img.crop(img.getbbox())
    
    width, height = img.size
    new_width = width + right + left
    new_height = height + top + bottom
    result = Image.new('RGBA', (new_width, new_height), (0, 0, 0, 0))
    result.paste(img, (left, top))
    return result

def add_pose_numbers(pose_arr):
    unique_poses = list(set(pose_arr))
    pose_counts = dict([ (ele, 0) for ele in unique_poses ])
    new_pose_arr = list(pose_arr)
    for i in range(len(new_pose_arr)):
        pose_counts[new_pose_arr[i]] += 1
        new_pose_arr[i] = new_pose_arr[i] + str(pose_counts[new_pose_arr[i]] - 1).zfill(4)
    return new_pose_arr

def make_png_xml(imgpaths, pose_names, save_dir, character_name="Result", clip=False):
    try:
        # PNG stuff
        widths = []
        heights = []
        exceptionmsg = None
        for impath in imgpaths:
            try:
                im = Image.open(impath)
            except Exception as e:
                exceptionmsg = str(e)
                print("Error: ", exceptionmsg)
                return 1, exceptionmsg
            else:
                if not clip:
                    widths.append(im.width + 4) # 2 pixels padding on each side
                    heights.append(im.height + 4)
                else:
                    box = im.getbbox()
                    widths.append(box[2] - box[0] + 4)
                    heights.append(box[3] - box[1] + 4)
                im.close()
        row_width_sums = []
        for i in range(0, len(widths), 4):
            row_width_sums.append(sum(widths[i:i+4]))
        final_img_width = max(row_width_sums)

        max_heights = []
        for i in range(0, len(heights), 4):
            max_heights.append(max(heights[i:i+4]))
        final_img_height = sum(max_heights)

        # XML Stuff
        root = ET.Element("TextureAtlas")
        root.tail = '\n' # os.linesep
        root.attrib['imagePath'] = character_name + ".png"

        final_img = Image.new('RGBA', (final_img_width, final_img_height), color=(0, 0, 0, 0))
        print("Final image size: ({}, {})".format(final_img_width, final_img_height))
        num_cols = 4
        csx = csy = 0
        newPoseNames = add_pose_numbers(pose_names)
        for i, imgpath in enumerate(imgpaths):
            print("Adding {} to final_image...".format(imgpath))
            try:
                old_img = Image.open(imgpath)
            except Exception as e:
                exceptionmsg = str(e)
                return 1, exceptionmsg
            else:
                new_img = pad_img(old_img, clip)

                row = i // num_cols
                col = i % num_cols

                if col == 0:
                    csx = 0
                csy = sum(max_heights[:row])
                
                subtexture_element = ET.Element("SubTexture")
                subtexture_element.tail = '\n' # os.linesep
                subtexture_element.attrib = {
                    "name" : character_name + " " + newPoseNames[i],
                    "x": f'{csx}',
                    "y": f'{csy}',
                    "width": f'{new_img.width}',
                    "height": f'{new_img.height}',
                    "frameX": '0',
                    "frameY": '0',
                    "frameWidth": f'{new_img.width}',
                    "frameHeight": f'{new_img.height}',
                }
                root.append(subtexture_element)

                new_img = new_img.convert('RGBA')
                final_img.paste(new_img, (csx, csy))
                
                csx += new_img.width
                
                old_img.close()
                new_img.close()

        # Saving png
        print(f"Saving final image....")
        # final_img.save(os.path.join(save_dir, character_name) + ".png")
        try:
            final_img.save(save_dir + '\\' + character_name + ".png")
        except Exception as e:
            exceptionmsg = str(e)
            return 1, exceptionmsg
        else:
            final_img.close()

        # Saving XML
        print("Saving XML")
        xmltree = ET.ElementTree(root)
        # with open(os.path.join(save_dir, character_name) + ".xml", 'wb') as f:
        try:
            with open(save_dir + '\\' + character_name + ".xml", 'wb') as f:
                xmltree.write(f, xml_declaration=True, encoding='utf-8')
            print("Done!")
        except Exception as e:
            exceptionmsg = str(e)
            return 1, exceptionmsg
    
    except Exception as e:
        exceptionmsg = str(e)
        return 1, exceptionmsg
    else:
        return 0, None

def clean_up(*args):
    for img in args:
        img.close()

def appendIconToIconGrid(icongrid_path, iconpaths, iconsize=150):
    ''' 
        Adds the selected Icon into the icon grid. Returns a value based on if it was successful or not, as follows:
        0 : Successful addition!
        1 : Icon grid (possibly) too full
        2 : Icon is too big to fit neatly into the icon grid
        3 : An Error occured in finding the right row to insert (It is possible that the icon grid wasn't transparent)
        4 : Icon image was too small for the icon space (This is a warning not an error, as the app will center the image if this happens)
    '''
    print("Icongrid from: {} \nIcons:  {}".format(icongrid_path, len(iconpaths)))
    retval = 0
    problem_img = None
    indices = []
    exception_msg = None
    for iconpath in iconpaths:
        icongrid = Image.open(icongrid_path)
        grid_w, grid_h = icongrid.size
        max_col = grid_w // iconsize
        max_row = grid_h // iconsize
        iconimg = Image.open(iconpath)
        new_index = None

        # Icongrid manipulation code
        lastrow_y = icongrid.getbbox()[-1] # lower bound of the bbox is on the last row
        dat = list(icongrid.getdata())
        lastrow_data = dat[-icongrid.width:len(dat)]
        secondlastrow_data = dat[-2*icongrid.width:-icongrid.width]
        print(f"Last row: {set(lastrow_data)}, Second last row: {set(secondlastrow_data)}")
        print(f"lastrow_y: {lastrow_y}, Image height: {icongrid.height}")
        if lastrow_y >= icongrid.height:
            clean_up(icongrid, iconimg)
            return 1, new_index, None, exception_msg # 1, None, None, None
        row_index = lastrow_y // iconsize

        last_row_img = icongrid.crop((0, row_index*iconsize, icongrid.width, row_index*iconsize + iconsize))
        box = last_row_img.getbbox()
        last_row_img.close()

        if box:
            lastrow_x = box[2]
            col_index = lastrow_x // iconsize

            if row_index >= max_row - 1 and col_index >= max_col - 1:
                print(f"row_index: {row_index}, col_index: {col_index}\nmax_row: {max_row}, max_col: {max_col}")
                return 1, new_index, None, exception_msg

            new_index = row_index*10 + col_index + 1

            newrow_index = new_index // 10
            newcol_index = new_index % 10
            print("New pic to put at index={}: row={}, col={}".format(new_index, newrow_index, newcol_index))
            imgy, imgx = newrow_index*iconsize, newcol_index*iconsize
            print("Coords to put new pic: row={} col={}".format(imgy, imgx))
            
            print("Pasting new img.....")
            # icongrid = icongrid.copy()
            # last ditch try catch block
            try:
                # icon size check
                w, h = iconimg.size
                if w > iconsize or h > iconsize:
                    clean_up(icongrid, iconimg)
                    problem_img = iconpath
                    return 2, new_index, problem_img, exception_msg # 2, None, iconpath
                if w != iconsize and h != iconsize:
                    print("Bad icon size....")
                    # we will try to center the smaller image into the grid space
                    dx = (iconsize//2) - (w//2)
                    dy = (iconsize//2) - (h//2)
                    imgx += dx
                    imgy += dy
                    iconimg = iconimg.convert('RGBA')
                    icongrid.paste(iconimg, (imgx, imgy, imgx+w, imgy+h))
                    # icongrid.save(os.path.join(savedir, "Result-icongrid.png"))
                    icongrid.save(icongrid_path)
                    clean_up(icongrid, iconimg)
                    retval = 4
                    problem_img = iconpath
                    indices.append(new_index)
                    # return 4, new_index, problem_img
                else:
                    iconimg = iconimg.convert('RGBA')
                    icongrid.paste(iconimg, (imgx, imgy, imgx+iconsize, imgy+iconsize))
                    indices.append(new_index)
                    # new_icongrid.save(os.path.join(savedir, "Result-icongrid.png"))
                    icongrid.save(icongrid_path)
                print("Done!")
            except Exception as e:
                print("Problem at try except block!")
                problem_img = iconpath
                exception_msg = str(e)
                return 1, indices, problem_img, exception_msg # 1, [...], iconpath

        else:
            print("Something's sus!")
            problem_img = iconpath
            return 3, indices, problem_img, exception_msg

        iconimg.close()
        icongrid.close()
    return retval, indices, problem_img, exception_msg

if __name__ == '__main__':
    print("This program is just the engine! To run the actual application, Please type: \npython xmlpngUI.py\nor \npython3 xmlpngUI.py \ndepending on what works")