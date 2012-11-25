    // Geolocation with HTML 5 and Google Maps API based on example from
    // maxheapsize: http://maxheapsize.com/2009/04/11/getting-the-browsers-geolocation-with-html-5/
    // This script is based in part on one from http://merged.ca/


    function getNear(squery, lat, lon, dist) {

      ajax_data = {
        location_query: squery,
        latitude: lat,
        longitude: lon,
        distance: dist
      };

      $.ajax({
        url: hostname_ + "get_nearby",
        success: function (data) {
          // alert('location search results: ' + data[0].addr + ': ' + data[0].lat + ', ' + data[0].lon);
          mapServiceProvider(lat, lon, dist, data);
        },
        data: ajax_data,
        dataType: "jsonp"
      });
    }

    function mapNear(latitude, longitude, qstring) {
        // Did we get the position correctly?
        // alert (position.coords.latitude+', '+position.coords.longitude);
        // show the map
        $('#map').css({ 'display': 'block'});
        var d = parseFloat($("#distance").val());
        var distance;
        if ($("#units").val() == "miles") {
          distance = d * 1.609344 * 1000;
        } else {
          distance = d * 1000;
        }      
        var squery = qstring + ' distance(author_location, geopoint(' + latitude + ', ' + longitude + ')) < ' + distance
        // submit search query
        getNear(squery, latitude, longitude, distance);
    }

    function findLocation() { 
      
      var qstring = $("#query").val();

      if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition( function (position) {

          mapNear(position.coords.latitude, position.coords.longitude, qstring);
          
        }, // next function is the error callback
          function (error)
          {
            switch(error.code) 
            {
              case error.TIMEOUT:
                alert ('Timeout');
                break;
              case error.POSITION_UNAVAILABLE:
                alert ('Position unavailable; using fake data (37.60, -122).  If you are running from localhost, note that geosearch is not currently fully supported on the dev app server.');
                mapNear(37.60, -122, qstring);
                break;
              case error.PERMISSION_DENIED:
                alert ('Permission denied; using fake data.(-33.873038, 151.20563).  If you are running from localhost, note that geosearch is not currently fully supported on the dev app server.');
                mapNear(-33.873038, 151.20563, qstring);
                break;
              case error.UNKNOWN_ERROR:
                alert ('Unknown error');
                break;
            }
          }
        );
      } 
      else  {
        alert("Geolocation services are not supported by your browser or you do not have a GPS device in your computer. Using fake data.");
        mapNear(-33, 151, qstring);

      }  
    }

    function createMarker(map, point, title, text) {

      var marker = new google.maps.Marker({
        position: point,
        map: map,
        title: title,
        });
      var infowindow = new google.maps.InfoWindow({
        content: "<p class=\"infowindow\">" + text + '</p>'
      });
      google.maps.event.addListener(marker, "click", function() {
        infowindow.open(map, marker);
      });
      return marker;
    }


    function mapServiceProvider(latitude,longitude, distance, data) {
      var userloc = new google.maps.LatLng(latitude,longitude);
      var mapOptions = {
        zoom: 4,
        center: userloc,
        mapTypeId: google.maps.MapTypeId.ROADMAP,
      }
      var map = new google.maps.Map(document.getElementById("map"),
        mapOptions);
      var latlngbounds = new google.maps.LatLngBounds();
      latlngbounds.extend(userloc);
      for (var i = 0; i < data.length; i++) {
        var p = new google.maps.LatLng(data[i].lat, data[i].lon);
        latlngbounds.extend(p);
        var author = data[i].author;
        var post_content = data[i].post_content;
        var marker = createMarker(map, p, author, post_content);
        marker.setMap(map);
      }
      // build blue-colored point for the user's location.
      var styleIconClass = new StyledIcon(StyledIconTypes.CLASS,{color:"#016DCF"});
      var youarehere = new StyledMarker({styleIcon:new StyledIcon(StyledIconTypes.MARKER,{},styleIconClass),position:userloc, map:map, title: 'you'});
        map.fitBounds(latlngbounds);
    }
