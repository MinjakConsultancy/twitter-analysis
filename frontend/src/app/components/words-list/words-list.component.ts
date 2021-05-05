import { Component, OnInit } from '@angular/core';
import { Word } from 'src/app/models/word.model';
import { SentimentService } from 'src/app/services/sentiment.service';
import { MatTableDataSource } from "@angular/material/table";
import {MatSliderChange} from "@angular/material/slider"
import {SelectionModel} from '@angular/cdk/collections';

@Component({
  selector: 'app-words-list',
  templateUrl: './words-list.component.html',
  styleUrls: ['./words-list.component.css']
})
export class WordsListComponent implements OnInit {

  dataSource = new MatTableDataSource<Word>();//   new SentimentDataSource(this.sentimentService);;
  selection  = new SelectionModel<Word>(true, []);
  dtOptions: any = {};
  displayedColumns  :  string[] = [ 'select', 'word', 'count', 'pos', 'sentiment', 'denial'];

  constructor(private sentimentService: SentimentService) { 
    //this.dataSource 

  }
  /** Whether the number of selected elements matches the total number of rows. */
isAllSelected() {
  const numSelected = this.selection.selected.length;
  const numRows = this.dataSource.data.length;
  return numSelected == numRows;
}

/** Selects all rows if they are not all selected; otherwise clear selection. */
masterToggle() {
  this.isAllSelected() ?
      this.selection.clear() :
      this.dataSource.data.forEach(row => this.selection.select(row));
}

  // formatLabel(value: number) {
  //   switch(value)
  //   {case -10:  return 'Negatief'
  //    case 0:  return 'Neutraal'
  //    case 10:  return 'Positief'
  //   }
  //   return '';
  // }
  
  ngOnInit(): void {
    this.retrieveWords();
    //this.dataSource.loadWords();
  }

  retrieveWords(): void {
    this.sentimentService.getAll()
      .subscribe(
        data => {
          data.sentiment = 0;
          data.denial = false;
          this.dataSource.data = data;
          //this.words = data;
          console.log(data);
        },
        error => {
          console.log(error);
        });
  }

  onInputChange(event: MatSliderChange) {
    console.log("This is emitted as the thumb slides");
    console.log(event.value);
  //  console.log(event.source.vertical=true)
  }

  updateWords(){
    console.log('startupdating');
    this.selection.selected.forEach( value => {
      console.log(value.id + "-" + value.sentiment);
      this.updateWord(value);
    });
    this.retrieveWords();
    this.selection.clear();
  }

  updateWord(word:Word){
    this.sentimentService.update(word.id, word).subscribe();

    //this.retrieveWords();
  }
  // refreshList(): void {
  //   this.retrieveWords();
  //   this.currentWord = undefined;
  //   this.currentIndex = -1;
  // }

  // setActiveTutorial(word: Word, index: number): void {
  //   this.currentWord = word;
  //   this.currentIndex = index;
  // }

}
