import { useRef, useState } from 'react';


export const useUploadedDocuments = () => {
    
    let [documents , setDocuments] = useState([]);
    let [currentDocument , setCurrentDocument] = useState(null);
    const pollerRef = useRef(null)

    async function fetchDocuments() {
 
        const response = await fetch("http://127.0.0.1:8000/api/v1/uploads/me", {
            method: "GET",
            credentials : "include"
          });
        
        const data = await response.json();
        setDocuments(data)
        
        let unprocessedDocuments = [];

        for (let index = 0; index < data.length; index++) {
            const doc = data[index];
            if (doc.status != "processed")unprocessedDocuments.push({doc , index})
        }
        
        if(unprocessedDocuments.length == 0)return;

        pollerRef.current = setInterval(async () => {
            
            if(unprocessedDocuments.length == 0) {
                 clearInterval(pollerRef.current)
                 pollerRef.current = null;
                 return;
            }
           
           for(let i = 0 ; i < unprocessedDocuments.length ; i++) { 
            const {doc , index} = unprocessedDocuments[i];
            let res = await fetch(`http://127.0.0.1:8000/api/v1/uploads/is-processed/${doc.id}`);
            let newDoc = await res.json()
            setDocuments( prev => prev.map( (item , j) => 
                                    j == index ? newDoc : item ) )

            if(newDoc.status == "processed") {
                unprocessedDocuments.splice(i , 1);
            }
           }

           

        } , 3500) 
        
        // if(unprocessedDocuments > 0) {
        //     const pollerRef = useRef(null)
        //     pollerRef.current = setInterval( () => {
                
                

        //     } , 500 )
        // }
    }
  
    return {documents , setDocuments , currentDocument , setCurrentDocument , fetchDocuments , pollerRef}
}