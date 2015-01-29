var express = require('express');
var router = express.Router();
var soap = require('soap');
var SOAP_URL = 'http://t-services.mobilion.com.tr/DiyanetServicePub/DynNamazVakitService.asmx?WSDL';

var ironio = require('node-ironio')(process.env.IRON_CACHE_TOKEN), 
    project = ironio.projects(process.env.IRON_CACHE_PROJECT_ID),
    cache = project.caches('service-cache');


var getCacheKey = function (req) {
    return encodeURIComponent(req.url.substring(1));
};

// checks the cache for url. if request found in cache 
// returns cached value otherwise returns null
var tryCache = function(req,res,fetchAndCache) {
  cache.get(getCacheKey(req), function(err, val) {
    var response;
    if(err || typeof(val) === 'undefined') {
      console.error("Not found in cache: "+getCacheKey(req));
      response = fetchAndCache(res);
    } else {
      console.log("Found in cache: "+getCacheKey(req)+"=>"+val);
    }
    res.json(response);
  });
};

/* GET home page. */
router.get('/', function(req, res) {
  res.render('index');
});

router.get('/ulkeler', function(req,res) {
  cache.get(getCacheKey(req), function(err, val) {
    if(err || typeof(val) === 'undefined') { // not found in cache
     console.error("Not found in cache: "+getCacheKey(req));
     soap.createClient(SOAP_URL, function(err, client) {
         client.DiyanetService.DiyanetServiceSoap.GetUlkeler({filter:""}, 
          function(err, result) {
             if(typeof result.GetUlkelerResult != 'undefined') {
               var response = result.GetUlkelerResult.UlkeItem;
               cache.put(getCacheKey(req), JSON.stringify(response), function(err) {
                   if (err) {
                     console.error('Failed to put to cache. ', err);
                   } else
                     console.log("successfully put cache");
               });
               res.json(response);
             }
             else
               res.status(500).json({ error: 'Ülkeler listesi alınamadı.' });
          });
     });
    } else { // found in cache
     console.log("Found in cache: "+getCacheKey(req));
     res.json(JSON.parse(val));
    }
  }); 
});

router.get('/eyaletler', function(req,res) {
  cache.get(getCacheKey(req), function(err, val) {
    if(err || typeof(val) === 'undefined') { // not found in cache
     console.error("Not found in cache: "+getCacheKey(req));
     soap.createClient(SOAP_URL, function(err, client) {
         client.DiyanetService.DiyanetServiceSoap.GetEyaletler({ulkeKodu: req.query.ulke, filter:""}, 
          function(err, result) {
             if(typeof result.GetEyaletlerResult != 'undefined') {
               var response = result.GetEyaletlerResult.EyaletItem;
               cache.put(getCacheKey(req), JSON.stringify(response), function(err) {
                   if (err) {
                     console.error('Failed to put to cache. ', err);
                   } else
                     console.log("successfully put cache");
               });
               res.json(response);
             }
             else
               res.status(500).json({ error: 'Eyaletler listesi alınamadı.' });
          });
     });
    } else { // found in cache
     console.log("Found in cache: "+getCacheKey(req));
     res.json(JSON.parse(val));
    }
  });
});

router.get('/sehirler', function(req,res) {  
  cache.get(getCacheKey(req), function(err, val) {
    if(err || typeof(val) === 'undefined') { // not found in cache
     console.error("Not found in cache: "+getCacheKey(req));
     soap.createClient(SOAP_URL, function(err, client) {
         client.DiyanetService.DiyanetServiceSoap.GetSehirler({ulkeKodu: req.query.ulke, eyaletKod: req.query.eyalet, filter:""}, 
          function(err, result) {
             if(typeof result.GetSehirlerResult != 'undefined') {
               var response = result.GetSehirlerResult.SehirItem;
               cache.put(getCacheKey(req), JSON.stringify(response), function(err) {
                   if (err) {
                     console.error('Failed to put to cache. ', err);
                   } else
                     console.log("successfully put cache");
               });
               res.json(response);
             }
             else
               res.status(500).json({ error: 'Şehirler listesi alınamadı.' });
          });
     });
    } else { // found in cache
     console.log("Found in cache: "+getCacheKey(req));
     res.json(JSON.parse(val));
    }
  });
});

router.get('/vakitler', function(req,res) {
    cache.get(getCacheKey(req), function(err, val) {
      if(err || typeof(val) === 'undefined') { // not found in cache
       console.error("Not found in cache: "+getCacheKey(req));
       soap.createClient(SOAP_URL, function(err, client) {
           client.DiyanetService.DiyanetServiceSoap.GetVakitler({sehirId: req.query.sehir, saatFarki: req.query.saat | 0}, 
            function(err, result) {
               if(typeof result.GetVakitlerResult != 'undefined') {
                 var response = result.GetVakitlerResult.DateItem;
                 cache.put(getCacheKey(req), JSON.stringify(response), function(err) {
                     if (err) {
                       console.error('Failed to put to cache. ', err);
                     } else
                       console.log("successfully put cache");
                 });
                 res.json(response);
               }
               else
                 res.status(500).json({ error: 'Vakitler alınamadı.' });
            });
       });
      } else { // found in cache
       console.log("Found in cache: "+getCacheKey(req));
       res.json(JSON.parse(val));
      }
    });
});

router.get('/last-updated', function(req,res) {
    var https = require('https');
    https.get(
        {
            host: 'api.github.com',
            path: '/repos/furkantektas/EzanVaktiAPI',
            port: 443,
            headers: {
                'User-Agent': 'EzanVaktiAPI'
        }}, function(response) {
                var body = '';
                response.on('data', function(d) {
                    body += d;
                });
                response.on('end', function() {
                    try {
                        var repoInfo = JSON.parse(body);
                    } catch (err) {
                        console.error('Unable to parse response as JSON', err);
                        res.status(500).json({error: "Bir hata oluştu. Lütfen daha sonra tekrar deneyiniz."});
                        return;
                    }
                    res.json({'last-updated':repoInfo.updated_at});
                });
            }).on('error', function(err) {
                console.error('Unable get repository info', err);
                res.status(500).json({error: "Bir hata oluştu. Lütfen daha sonra tekrar deneyiniz."});
            });
});

module.exports = router;
