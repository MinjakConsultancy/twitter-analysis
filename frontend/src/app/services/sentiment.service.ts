import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from './../../environments/environment';

const baseUrl = environment.sentimentAPIUrl;

@Injectable({
  providedIn: 'root'
})
export class SentimentService {

  constructor(private http: HttpClient) { }

  getAll(): Observable<any> {
    return this.http.get(baseUrl+'/notSpecified');
  }

  update(id: any, data: any): Observable<any> {
    console.log('update '+ id);
    console.log(`${baseUrl}/${id}`);
    
    return this.http.put(`${baseUrl}/${id}`, data,{responseType: 'text'});
  }

}