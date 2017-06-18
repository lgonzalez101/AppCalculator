using AppWebApi.Models;
using Newtonsoft.Json;
using RestSharp;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Threading.Tasks;
using System.Web;
using System.Web.Mvc;

namespace AppWebApi.Controllers
{
    public class HomeController : Controller
    {
        public ActionResult Index()
        {
            //var _client = new RestClient { BaseUrl = new Uri("http://localhost:61554/") };
            //var request = new RestRequest("api/values", Method.GET) { RequestFormat = DataFormat.Json };
            //var response = _client.Execute<ResultadoViewModel>(request);
            //if (response.Data == null)
            //    throw new Exception(response.ErrorMessage);          
            return View();
        }

        [HttpGet]
        public ActionResult Calcular(ResultadoViewModel model)
        {
            var  _client = new RestClient { BaseUrl = new Uri("http://apiservicecalculator.apphb.com/") };
            var request = new RestRequest("api/values", Method.POST) { RequestFormat = DataFormat.Json };
            request.AddBody(model);
            var response = _client.Execute<ResultadoViewModel>(request);
            if (response.StatusCode != HttpStatusCode.Created)
            {
                return Json(response.Data, JsonRequestBehavior.AllowGet);
            }
                throw new Exception(response.ErrorMessage);

        }

        public ActionResult About()
        {
            ViewBag.Message = "Your application description page.";

            return View();
        }

        public ActionResult Contact()
        {
            ViewBag.Message = "Your contact page.";

            return View();
        }
    }
}