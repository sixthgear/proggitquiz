var timer_stack = []

function zeropad(number, width) {
    width -= number.toString().length;
    if ( width > 0 )
        return new Array( width + (/\./.test( number ) ? 2 : 1) ).join( '0' ) + number;  
    return number + ""; // always return a string
}

function Timer(element, initial, callback) {
    var self = this;
    this.inital = initial; // milliseconds started with
    this.started = Date.now();
    this.element = element;
    this.callback = callback;
    this.timer_id = window.setInterval(function(){      
        var elapsed = Date.now() - self.started;
        var ms = self.inital - elapsed;
        self.display(ms);
        if (ms <= 0) {            
            self.stop();
            self.callback();
        }        
    }, 1000);
    self.display(initial);
}

Timer.prototype.stop = function() {
    window.clearInterval(this.timer_id);
}

Timer.prototype.display = function(ms) {
    ms = Math.max(0, Math.min(300000, ms));
    var min = Math.floor(ms / 1000 / 60);
    var sec = Math.floor(ms / 1000 % 60);
    $(this.element).html(min + ":" + zeropad(sec, 2));
}

$(document).ready(function(){


    // TODO: ajax refesh this content instead of reloading the whole page
    $(".btn-refresh").click(function(e){
        $(this).html('Downloading...');
        window.setTimeout(function(){
            location.reload(true);
        }, 5000);
    });

    $(".timer-running span").each(function(i, el) {
        var str = $(el).html();        
        var parts = str.split(":");
        var seconds = parseInt(parts[0]) * 60;
        seconds += parseInt(parts[1]);                
        var t = new Timer(this, seconds*1000, function(){ 
            window.setTimeout(function() {location.reload(true)}, 500);
        });
        timer_stack.push(t);
    });

});
