  document.addEventListener('DOMContentLoaded', () => {

      // Connect to websocket
      var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port);

      // When connected, configure buttons
      socket.on('connect', () => {

          // Each button should emit a "submit vote" event
          document.querySelectorAll('button').forEach(button => {
              button.onclick = () => {
                  //move_all();

                  const option = button.dataset.channel;
                  // send new message
                  if (option == 'sendmes') {
                    let mes = document.getElementById('message_box').value;
                    let pin = localStorage.getItem('pin_localstore');
                    mes_to_send = {"message":mes, "pin":pin, "delete":false}
                    socket.emit('send message', mes_to_send);
                    document.getElementById('message_box').value = "";
                  }
                  // create new channel
                  if (option == 'createchan') {
                    let mes = document.getElementById('create_box').value;
                    socket.emit('create channel', mes);
                    document.getElementById('create_box').value = "";
                  }

                  if (option == 'leave') {
                    localStorage.removeItem('userschannel_localstore');
                    window.location.href = '/list_channels';
                    //TODO: remove user from channel
                  }

                  if (option == 'logout') {
                    localStorage.removeItem('username_localstore');
                    localStorage.removeItem('userschannel_localstore');
                    window.location.href = '/logout';
                  }
              };
          });
      });

      // message received
      socket.on('message new', mdata => {
        // Create new post.
        //var my_channel = window.location.search.substring(6);
        var my_channel = localStorage.getItem('userschannel_localstore');
        var message = mdata["post"];
        var datetime = mdata["time"];
        var channel = mdata["channel"];
        var user = mdata["user"];
        var post_id = mdata["post_id"];
        console.log(message)
        if (channel == my_channel){
          const post = post_template({'user':user, 'contents': message, 'time':datetime, 'post_id':post_id});
          // Add post to DOM.
          prev_posts = document.querySelector('#posts').innerHTML;
          all_posts = post + prev_posts;
          document.querySelector('#posts').innerHTML = all_posts;
        }
      });

      // message deletion received
      socket.on('message removed', rdata => {
        status = rdata["status"];
        sender = rdata["sender"];
        post_id = rdata["post_id"];

        if (status == 1){
          //post_id = parent.getElementsByClassName("post_id")[0].innerHTML;
          let l = document.getElementsByClassName("post").length;
          //console.log(l)
          for (i=0; i<l; i++){
            var el = document.getElementsByClassName("post")[i];
            var iter_post_id = el.getElementsByClassName("post_id")[0].innerHTML;
            //console.log(iter_post_id)
            if (iter_post_id == post_id){
              el.remove();
              break;
            }
          }

        }

        if (sender == localStorage.getItem('username_localstore')){
          if (status == 0)
            window.alert("Post NOT deleted!");
          else if (status == 1)
            window.alert("Post deleted!");
          else if (status == 2)
            window.alert("Authorization Error: You don't seem to be the owner of this post!");
        }
      });


      // new channel received
      socket.on('channel new', cndata => {
        var status = cndata["status"]
        if (status == 0)
          window.alert("channel name already in use")
        if (status == 1){
          // Create new post.
          var channel_name = cndata["channel_name"]
          var datetime = cndata["time"]

          const post = post_template({'contents': channel_name});
          // Add post to DOM.
          //console.log(post);
          prev_posts = document.querySelector('#chans').innerHTML;
          all_posts = post + prev_posts;
          document.querySelector('#chans').innerHTML = all_posts;
        }
      });


      window.onresize = () => {

      };


  });
