var express = require('express');
var router = express.Router();
var soap = require('soap');
var SOAP_URL = 'http://t-services.mobilion.com.tr/DiyanetServicePub/DynNamazVakitService.asmx?WSDL';

/* GET home page. */
router.get('/', function(req, res) {
  res.render('index', { title: 'Express' });
});

router.get('/ulkeler', function(req,res) {
    soap.createClient(SOAP_URL, function(err, client) {
        console.log(client.describe());
        client.DiyanetService.DiyanetServiceSoap.GetUlkeler({filter:""}, function(err, result) {
            if(typeof result.GetUlkelerResult != 'undefined')
                res.json(result.GetUlkelerResult.UlkeItem);
            else
                res.status(500).json({ error: 'Ülkeler listesi alınamadı.' });
        });
    });
});

router.get('/eyaletler', function(req,res) {
    soap.createClient(SOAP_URL, function(err, client) {
        client.DiyanetService.DiyanetServiceSoap.GetEyaletler({ulkeKodu: req.query.ulke, filter:""}, function(err, result) {
            if(typeof result.GetEyaletlerResult != 'undefined')
                res.json(result.GetEyaletlerResult.EyaletItem);
            else
                res.status(500).json({ error: 'Eyaletler listesi alınamadı.' });
        });
    });
});

router.get('/sehirler', function(req,res) {
    soap.createClient(SOAP_URL, function(err, client) {
        client.DiyanetService.DiyanetServiceSoap.GetSehirler({ulkeKodu: req.query.ulke, eyaletKod: req.query.eyalet, filter:""}, function(err, result) {
            if(typeof result.GetSehirlerResult != 'undefined')
                res.json(result.GetSehirlerResult.SehirItem);
            else
                res.status(500).json({ error: 'Şehirler listesi alınamadı.' });
        });
    });
});

router.get('/vakitler', function(req,res) {
    soap.createClient(SOAP_URL, function(err, client) {
        client.DiyanetService.DiyanetServiceSoap.GetVakitler({sehirId: req.query.sehir, saatFarki: req.query.saat | 0}, function(err, result) {
            if(typeof result.GetVakitlerResult != 'undefined')
                res.json(result.GetVakitlerResult.DateItem);
            else
                res.status(500).json({ error: 'Vakitler alınamadı.' });
        });
    });
});

router.get('/version', function(req,res) {
    var version = 0;
    if(typeof process.env.HEROKU_RELEASE_NAME != 'undefined')
        version = process.env.HEROKU_RELEASE_NAME.slice(1);
    res.json({version: version});
});

module.exports = router;
