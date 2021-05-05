import { TestBed } from '@angular/core/testing';
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Word } from '../models/word.model';
import { SentimentService } from './sentiment.service';

describe('SentimentService', () => {
  let service: SentimentService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(SentimentService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
