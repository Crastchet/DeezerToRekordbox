#!/usr/bin/python
# -*-coding:utf-8 -*

import requests
import json
from lxml import etree
import sys


def getPlaylists_Id_Title_FromUser(userId):
    requ = requests.get('https://api.deezer.com/user/{}/playlists'.format(userId))
    resp = requ.json()

    playlists_id_title = []
    for playlist in resp['data']:
        playlists_id_title.append( {
            'id':playlist['id'],
            'title':playlist['title']
        } )

    return playlists_id_title


def getTracksFromPlaylistId(playlistId):
    requ = requests.get('https://api.deezer.com/playlist/{}/tracks'.format(playlistId))
    resp = requ.json()

    tracks = []
    while resp != None:
        for track in resp['data']:
            tracks.append( {
                'id':track['id'],
                'title':track['title'],
                'artist':track['artist']['name'] # Here I made the choice to only keep artist.name, and not the object artist (will change to make match more accurate)
            } )
        if 'next' in resp:
            requ = requests.get(resp['next'])
            resp = requ.json()
        else:
            resp = None

    return tracks


def getPlaylists_Tracks_FromUser(userId):
    playlists = []
    playlists_id_title = getPlaylists_Id_Title_FromUser(userId)

    for playlist_id_title in playlists_id_title:
        playlists.append( {
            'infos':playlist_id_title,
            'tracks':getTracksFromPlaylistId(playlist_id_title['id'])
        } )

    return playlists


# Extract the tracks from the file generated with RekordBox
def getAllTracksFromCollection(xmlFile):
    tree = etree.parse(xmlFile)
    tracks = []
    for track in tree.xpath("/DJ_PLAYLISTS/COLLECTION/TRACK"):
        tracks.append( {
            'TrackID':track.get("TrackID"),
            'Name':track.get("Name"),
            'Artist':track.get("Artist")
        } )
    return tracks


# Find in which playlists a track from RekordBox appears
def findPlaylists_Title_ForTrack(playlists, track_to_find):
    playlists_title_to_return = []
    for playlist in playlists:
        for track in playlist['tracks']:
            if track_to_find['Name'] == track['title'] and track_to_find['Artist'].split("/")[0] == track['artist']:
                playlists_title_to_return.append(playlist['infos']['title'])
                break
    return playlists_title_to_return


def generateCollectionPlaylists(playlists,tracks):
    collection_playlists = {}
    for track in tracks:
        for playlist in findPlaylists_Title_ForTrack(playlists,track):
            if playlist in collection_playlists:
                collection_playlists[playlist].append(track['TrackID'])
            else:
                collection_playlists[playlist] = [ track['TrackID'] ]
    return collection_playlists


def addPlaylistsIntoXML(collection_playlists, fileName):
    tree = etree.parse(fileName)

    node_playlists_root = tree.xpath("/DJ_PLAYLISTS/PLAYLISTS/NODE")[0]
    node_playlists_root.set("Count", str( len(collection_playlists) ))
    for playlistTitle in collection_playlists:
        node_playlists_root_playlist = etree.SubElement(node_playlists_root, "NODE")
        node_playlists_root_playlist.set("Name", playlistTitle)
        node_playlists_root_playlist.set("Type", "1")
        node_playlists_root_playlist.set("KeyType", "0")
        node_playlists_root_playlist.set("Entries", str(len(collection_playlists[playlistTitle])))
        for trackID in collection_playlists[playlistTitle]:
            track = etree.SubElement(node_playlists_root_playlist, "TRACK")
            track.set("Key", trackID)

    node_djplaylists = tree.xpath("/DJ_PLAYLISTS")[0]

    # file = open('new_'+fileName, "w")
    et = etree.ElementTree(node_djplaylists)
    et.write('new_'+fileName, pretty_print=True, xml_declaration=True, encoding="utf-8")


if __name__ == "__main__":
    print(type(sys.argv[0]))
    print(type(sys.argv[1]))
    print(type(sys.argv[2]))
    # Load the tracks fom RekordBox
    tracks = getAllTracksFromCollection(sys.argv[2])
    # Load the playlist of user
    playlists = getPlaylists_Tracks_FromUser(sys.argv[1])
    # Match playlists with RekorBox's tracks
    collection_playlists = generateCollectionPlaylists(playlists,tracks)
    # Write in xml file for RekordBox
    addPlaylistsIntoXML(collection_playlists,sys.argv[2])
